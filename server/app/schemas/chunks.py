import uuid
from typing import Any

from pydantic import BaseModel, Field


class ChunkPreview(BaseModel):
	id: uuid.UUID
	document_id: uuid.UUID
	content: str
	token_count: int | None
	metadata: dict[str, Any] | None = Field(
		default=None,
		validation_alias='chunk_metadata',
		serialization_alias='metadata',
	)

	model_config = {'from_attributes': True, 'populate_by_name': True}


class ChunkListResponse(BaseModel):
	items: list[ChunkPreview]
	total: int
