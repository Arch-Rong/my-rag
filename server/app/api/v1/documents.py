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

router = APIRouter(prefix='/documents', tags=['documents'])


@router.get('', response_model=DocumentListResponse)
def list_documents(
	limit: int = 100,
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_session),
) -> DocumentListResponse:
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
		background_tasks.add_task(run_ingest_for_document, document.id)
	return document


@router.get('/{document_id}', response_model=DocumentResponse)
def get_document(
	document_id: uuid.UUID,
	current_user: User = Depends(get_current_user),
	session: Session = Depends(get_session),
) -> Document:
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
	delete_document(session, storage, document_id, user_id=current_user.id)
