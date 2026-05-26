"""
知识库文档 HTTP 接口（需登录）。

路径前缀：/api/v1/documents

与 RAG 的关系：
  上传 → 后台 ingest（分片 + 可选向量化）→ chunks 表 → 聊天时向量检索。
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlmodel import Session, select

from app.auth.deps import get_current_user
from app.db.session import get_session
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.enums import DocumentStatus
from app.models.user import User
from app.schemas.chunks import ChunkListResponse, ChunkPreview
from app.schemas.documents import DocumentListResponse, DocumentResponse
from app.services.document_service import (
	assert_document_owner,
	create_document_upload,
	delete_document,
	get_document_file_bytes,
	get_document_or_404,
	list_library_documents,
	read_upload_bytes,
)
from app.config import get_settings
from app.services.ingest_service import ingest_document
from app.services.ingest_tasks import run_ingest_for_document
from app.storage.deps import get_object_storage
from app.storage.protocol import ObjectStorage

# 本模块所有路由挂在 /documents 下
router = APIRouter(prefix='/documents', tags=['documents'])


@router.get('', response_model=DocumentListResponse)
def list_documents(
	limit: int = 100,
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_session),
) -> DocumentListResponse:
	"""
	GET /api/v1/documents — 列出当前用户上传的文档。

	供前端「知识库」页展示：标题、status、chunk_count 等。
	前端会对 queued/parsing 状态轮询，直到变为 ready 或 failed。
	"""
	rows = list_library_documents(session, user_id=current_user.id, limit=limit)
	items = [DocumentResponse.model_validate(row) for row in rows]
	return DocumentListResponse(items=items, total=len(items))


@router.post('', response_model=DocumentResponse, status_code=201)
async def upload_document(
	background_tasks: BackgroundTasks,
	file: UploadFile = File(...),
	title: str | None = Form(default=None),
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_session),
	storage: ObjectStorage = Depends(get_object_storage),
) -> Document:
	"""
	POST /api/v1/documents — 上传文件（multipart：file + 可选 title）。

	流程：
	  1. 读文件字节 → 写入 MinIO/S3 → 插入 documents 行（通常 status=queued）
	  2. 若 INGEST_ON_UPLOAD=true，后台任务跑 ingest（解析、分片、向量化）
	  3. 立即返回文档元数据，不等待 ingest 完成

	注意：返回 ready 需等后台跑完；向量化是否成功要看 chunks.embedding（见 backfill 脚本）。
	"""
	data, filename = await read_upload_bytes(file)
	document = create_document_upload(
		session,
		storage,
		user_id=current_user.id,
		title=title,
		filename=filename,
		data=data,
	)
	if get_settings().ingest_on_upload:
		settings = get_settings()
		if settings.ingest_spawn_subprocess:
			# 在返回 201 前拉起子进程，不依赖 BackgroundTasks（reload 会杀掉进程内任务）
			# 日志见终端 app.services.ingest_tasks（需 LOG_LEVEL=INFO，main 已 configure_app_logging）
			run_ingest_for_document(document.id)
		else:
			background_tasks.add_task(run_ingest_for_document, document.id)
	return document


@router.get('/{document_id}', response_model=DocumentResponse)
def get_document(
	document_id: uuid.UUID,
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_session),
) -> Document:
	"""
	GET /api/v1/documents/{id} — 查询单条文档详情。

	仅能访问本人上传的文档（assert_document_owner）。
	"""
	document = get_document_or_404(session, document_id)
	assert_document_owner(document, current_user.id)
	return document


@router.post('/{document_id}/ingest', response_model=DocumentResponse)
def trigger_ingest(
	document_id: uuid.UUID,
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_session),
	storage: ObjectStorage = Depends(get_object_storage),
) -> Document:
	"""
	POST /api/v1/documents/{id}/ingest — 手动触发/重跑入库。

	适用：上传时未自动 ingest、status=failed 需重试、或想重新分片。
	同步执行 ingest_document（本次请求会等到分片结束；向量化在 ingest 内一并尝试）。
	"""
	document = get_document_or_404(session, document_id)
	assert_document_owner(document, current_user.id)
	if document.status not in (
		DocumentStatus.queued,
		DocumentStatus.failed,
		DocumentStatus.ready,
	):
		raise HTTPException(
			status_code=409,
			detail=f'cannot ingest while status is {document.status.value}',
		)
	try:
		return ingest_document(session, storage, document_id)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get('/{document_id}/chunks', response_model=ChunkListResponse)
def list_document_chunks(
	document_id: uuid.UUID,
	limit: int = 20,
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_session),
) -> ChunkListResponse:
	"""
	GET /api/v1/documents/{id}/chunks — 预览该文档的分片列表（正文片段）。

	用于调试或管理端查看 ingest 结果；默认最多 100 条。
	响应不含 embedding 字段，不能用来判断向量化是否成功（需查库或补向量脚本）。
	"""
	document = get_document_or_404(session, document_id)
	assert_document_owner(document, current_user.id)
	rows = session.exec(
		select(Chunk)
		.where(Chunk.document_id == document_id)
		.order_by(Chunk.created_at)
		.limit(min(limit, 100))
	).all()
	items = [ChunkPreview.model_validate(row) for row in rows]
	return ChunkListResponse(items=items, total=len(items))


@router.get('/{document_id}/file')
def download_document_file(
	document_id: uuid.UUID,
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_session),
	storage: ObjectStorage = Depends(get_object_storage),
) -> Response:
	"""
	GET /api/v1/documents/{id}/file — 下载原始上传文件。

	从对象存储读出字节流，带 Content-Disposition 附件文件名。
	"""
	document, data = get_document_file_bytes(
		session, storage, document_id, user_id=current_user.id
	)
	media_type = document.mime_type or 'application/octet-stream'
	filename = document.original_filename or 'download'
	return Response(
		content=data,
		media_type=media_type,
		headers={
			'Content-Disposition': f'attachment; filename="{filename}"',
		},
	)


@router.delete('/{document_id}', status_code=204)
def remove_document(
	document_id: uuid.UUID,
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_session),
	storage: ObjectStorage = Depends(get_object_storage),
) -> None:
	"""
	DELETE /api/v1/documents/{id} — 删除文档。

	软删或硬删由 document_service 实现：通常标记删除并清理存储与关联 chunks。
	成功时返回 204 无 body。
	"""
	delete_document(session, storage, document_id, user_id=current_user.id)
