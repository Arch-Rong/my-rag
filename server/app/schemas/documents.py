import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
	id: uuid.UUID
	user_id: uuid.UUID | None
	owner_type: str
	title: str
	original_filename: str | None
	source_type: str
	mime_type: str | None
	file_size: int | None
	file_path: str | None
	content_hash: str | None
	chunk_count: int
	status: str
	error_message: str | None
	created_at: datetime
	updated_at: datetime
	deleted_at: datetime | None = None

	model_config = {'from_attributes': True}


class DocumentListResponse(BaseModel):
	items: list[DocumentResponse]
	total: int = Field(description='当前页条数')
