import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlmodel import Session

from app.auth.deps import get_current_user
from app.db.session import get_session
from app.models.document import Document
from app.models.user import User
from app.schemas.documents import DocumentResponse
from app.services.document_service import (
	create_document_upload,
	delete_document,
	get_document_file_bytes,
	read_upload_bytes,
)
from app.storage.deps import get_object_storage
from app.storage.protocol import ObjectStorage

router = APIRouter(prefix='/documents', tags=['documents'])


@router.post('', response_model=DocumentResponse, status_code=201)
async def upload_document(
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
	return document


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
