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
	session: Session,  # 数据库会话
	scope: RetrievalScope,  # 聊天页选的检索范围：全部 / 教材 / 我的
	user_id: uuid.UUID | None,  # 当前用户；与 scope 一起决定「能看哪些文档」
) -> bool:
	"""
	判断：在当前 scope 内，是否至少有一条 chunk 已经写过向量（embedding）。

	用于 search_chunks_vector 的前置检查：
	  - 返回 True  → 可以走向量检索（embed_query + pgvector）
	  - 返回 False → 直接视为「未检索到」，只把用户问题交给模型

	注意：只检查「有没有向量」，不检查和你这问是否相关。
	"""
	# 与检索相同的文档范围：未删除、status=ready、按 scope 过滤教材/我的上传
	filters = document_scope_filters(scope, user_id, ready_only=True)
	count = session.exec(
		select(func.count())
		.select_from(Chunk)
		.join(Document, Chunk.document_id == Document.id)  # chunk 必须属于 scope 内的 document
		.where(*filters, Chunk.embedding.isnot(None))  # type: ignore[union-attr]
	).one()
	return int(count or 0) > 0
