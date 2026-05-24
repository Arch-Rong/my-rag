import uuid

from sqlalchemy import or_
from sqlmodel import Session, func, select

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.enums import DocumentStatus, OwnerType, RetrievalScope


def document_scope_filters(
	scope: RetrievalScope,
	user_id: uuid.UUID | None,
	*,
	ready_only: bool,
) -> tuple:
	not_deleted = Document.deleted_at.is_(None)  # type: ignore[union-attr]
	status_ok = Document.status != DocumentStatus.deleted
	filters: list = [not_deleted, status_ok]
	if ready_only:
		filters.append(Document.status == DocumentStatus.ready)

	if scope == RetrievalScope.system_only:
		filters.append(Document.owner_type == OwnerType.system)
	elif scope == RetrievalScope.user_only:
		if user_id is None:
			raise ValueError('user_only scope requires user_id')
		filters.extend(
			[Document.owner_type == OwnerType.user, Document.user_id == user_id]
		)
	else:
		if user_id is None:
			filters.append(Document.owner_type == OwnerType.system)
		else:
			filters.append(
				or_(
					Document.owner_type == OwnerType.system,
					(Document.owner_type == OwnerType.user) & (Document.user_id == user_id),
				)
			)
	return tuple(filters)


def scope_has_embeddings(
	session: Session,
	scope: RetrievalScope,
	user_id: uuid.UUID | None,
) -> bool:
	filters = document_scope_filters(scope, user_id, ready_only=True)
	count = session.exec(
		select(func.count())
		.select_from(Chunk)
		.join(Document, Chunk.document_id == Document.id)
		.where(*filters, Chunk.embedding.isnot(None))  # type: ignore[union-attr]
	).one()
	return int(count or 0) > 0
