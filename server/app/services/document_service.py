import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from sqlmodel import Session, delete

from app.config import Settings, get_settings
from app.models.document import Document
from app.models.enums import DocumentStatus, OwnerType, SourceType
from app.storage.keys import build_upload_key, allowed_extension, mime_for_filename
from app.storage.protocol import ObjectStorage


def _sha256_hex(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


def assert_document_owner(document: Document, user_id: uuid.UUID) -> None:
	if document.user_id != user_id or document.owner_type != OwnerType.user:
		raise HTTPException(status_code=403, detail='not allowed to access this document')


async def read_upload_bytes(
	file: UploadFile, settings: Settings | None = None
) -> tuple[bytes, str]:
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


def get_document_or_404(session: Session, document_id: uuid.UUID) -> Document:
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
