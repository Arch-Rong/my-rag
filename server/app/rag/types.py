from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from app.models.enums import DocumentStatus, OwnerType


@dataclass(frozen=True)
class ChunkHit:
	chunk_id: uuid.UUID
	document_id: uuid.UUID
	document_title: str
	owner_type: OwnerType
	content: str
	score: float
	metadata: dict[str, Any] | None


@dataclass(frozen=True)
class DocumentSummary:
	id: uuid.UUID
	title: str
	owner_type: OwnerType
	status: DocumentStatus
	chunk_count: int
	original_filename: str | None
