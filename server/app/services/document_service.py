"""
文档（知识库文件）相关的业务逻辑。

和 api/v1/documents.py 的分工：
  - api 层：收 HTTP 请求、返回 JSON（薄薄一层）
  - 本文件：真正干活——校验文件、写 MinIO、读写 documents/chunks 表

典型流程：
  上传 → read_upload_bytes → create_document_upload（MinIO + DB，status=queued）
  下载 → get_document_file_bytes（校验归属 + 从 MinIO 读字节）
  删除 → delete_document（删 MinIO 文件 + 删 chunks + 软删 documents）
"""

import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from sqlmodel import Session, delete, or_, select

from app.config import Settings, get_settings
from app.models.document import Document
from app.models.enums import DocumentStatus, OwnerType, SourceType
from app.storage.keys import build_upload_key, allowed_extension, mime_for_filename
from app.storage.protocol import ObjectStorage


def _sha256_hex(data: bytes) -> str:
	"""算文件内容的 SHA256，用于去重、判断文件是否改过。"""
	return hashlib.sha256(data).hexdigest()


def assert_document_owner(document: Document, user_id: uuid.UUID) -> None:
	"""
	权限检查：当前用户能不能操作这份文档。

	只允许：文档属于该用户（user_id 一致）且是用户上传库（owner_type=user）。
	系统预置教材（owner_type=system）不能通过用户接口下载/删除。
	不通过 → 403。
	"""
	if document.user_id != user_id or document.owner_type != OwnerType.user:
		raise HTTPException(status_code=403, detail='not allowed to access this document')


async def read_upload_bytes(
	file: UploadFile, settings: Settings | None = None
) -> tuple[bytes, str]:
	"""
	从上传的 multipart 文件里读出全部字节，并做基础校验。

	检查项：
	  - 不能为空
	  - 不能超过 max_upload_bytes（默认 50MB）
	  - 扩展名只能是 .pdf 或 .md

	返回：(文件二进制, 原始文件名)，交给 create_document_upload 使用。
	"""
	cfg = settings or get_settings()
	data = await file.read()
	if not data:
		raise HTTPException(status_code=400, detail='empty file')
	if len(data) > cfg.max_upload_bytes:
		raise HTTPException(
			status_code=413,
			detail=f'file exceeds max size ({cfg.max_upload_bytes} bytes)',
		)
	filename = file.filename or 'upload.bin'
	try:
		allowed_extension(filename)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	return data, filename


def create_document_upload(
	session: Session,
	storage: ObjectStorage,
	*,
	user_id: uuid.UUID,
	title: str | None,
	filename: str,
	data: bytes,
) -> Document:
	"""
	完成一次「用户上传」的完整入库（元数据 + 源文件）。

	步骤：
	  1. 生成 document_id，拼 MinIO 路径（uploads/用户id/文档id/文件名）
	  2. 把文件字节写入对象存储（MinIO 或本地）
	  3. 在 documents 表插入一行：status=queued（等待后续 Worker 解析、切块、向量化）

	注意：此时还没有 chunks，RAG 还不能检索这份文档。
	"""
	doc_id = uuid.uuid4()
	object_key = build_upload_key(user_id, doc_id, filename)
	mime = mime_for_filename(filename)

	storage.put_bytes(object_key, data, mime)

	document = Document(
		id=doc_id,
		user_id=user_id,
		owner_type=OwnerType.user,
		title=title or filename,
		original_filename=filename,
		source_type=SourceType.user_upload,
		mime_type=mime,
		file_size=len(data),
		file_path=object_key,
		content_hash=_sha256_hex(data),
		status=DocumentStatus.queued,
	)
	session.add(document)
	session.commit()
	session.refresh(document)
	return document


def list_library_documents(
	session: Session,
	*,
	user_id: uuid.UUID,
	limit: int = 100,
) -> list[Document]:
	"""
	知识库列表：系统预置教材 + 当前用户上传（均排除软删）。

	系统教材 owner_type=system；用户文件需 user_id 一致且 owner_type=user。
	按 created_at 倒序，最新在前。
	"""
	limit = min(max(limit, 1), 200)
	stmt = (
		select(Document)
		.where(
			Document.status != DocumentStatus.deleted,
			or_(
				Document.owner_type == OwnerType.system,
				(Document.user_id == user_id) & (Document.owner_type == OwnerType.user),
			),
		)
		.order_by(Document.created_at.desc())
		.limit(limit)
	)
	return list(session.exec(stmt).all())


def get_document_or_404(session: Session, document_id: uuid.UUID) -> Document:
	"""
	按 id 查文档；不存在或已软删则 404。

	下载、删除等接口都会先调这个，再去做权限、读文件等后续操作。
	"""
	document = session.get(Document, document_id)
	if document is None or document.status == DocumentStatus.deleted:
		raise HTTPException(status_code=404, detail='document not found')
	return document


def get_document_file_bytes(
	session: Session,
	storage: ObjectStorage,
	document_id: uuid.UUID,
	*,
	user_id: uuid.UUID,
) -> tuple[Document, bytes]:
	"""
	下载源文件：校验权限后，从 MinIO 读出 PDF/MD 的原始字节。

	返回 (Document 元数据, 文件内容)，api 层再包装成 HTTP 下载响应。
	MinIO 里路径丢了会 404 file not found in storage。
	"""
	document = get_document_or_404(session, document_id)
	assert_document_owner(document, user_id)
	if not document.file_path:
		raise HTTPException(status_code=404, detail='document has no file')
	try:
		data = storage.get_bytes(document.file_path)
	except FileNotFoundError as exc:
		raise HTTPException(status_code=404, detail='file not found in storage') from exc
	return document, data


def delete_document(
	session: Session,
	storage: ObjectStorage,
	document_id: uuid.UUID,
	*,
	user_id: uuid.UUID,
) -> None:
	"""
	删除用户自己的文档（软删 + 清理关联数据）。

	步骤：
	  1. 查文档，已删过的直接 return（幂等）
	  2. 校验必须是本人
	  3. 若 MinIO 里还有源文件 → 删掉
	  4. 删掉该文档下所有 chunks（含向量）
	  5. documents 行保留，但 status=deleted、填 deleted_at（审计/防误删）

	之后 RAG 检索必须过滤 deleted 和 deleted_at。
	"""
	document = session.get(Document, document_id)
	if document is None:
		raise HTTPException(status_code=404, detail='document not found')
	if document.status == DocumentStatus.deleted:
		return
	assert_document_owner(document, user_id)

	if document.file_path and storage.exists(document.file_path):
		storage.delete(document.file_path)

	from app.models.chunk import Chunk

	session.exec(delete(Chunk).where(Chunk.document_id == document_id))

	document.status = DocumentStatus.deleted
	document.deleted_at = datetime.now(timezone.utc)
	session.add(document)
	session.commit()
