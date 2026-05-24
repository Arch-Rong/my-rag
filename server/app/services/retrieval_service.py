"""
混合检索（Hybrid RAG）：

  路 A 密集：问题 → Embedding → pgvector 余弦相似度（ChunkVectorStore）
  路 B 稀疏：关键词字面匹配（BM25 简化版 ILIKE）
  融合：RRF（Reciprocal Rank Fusion）→ Top-K 交给 LLM
"""

from __future__ import annotations

import uuid

from sqlmodel import Session, select

from app.config import get_settings
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.enums import OwnerType, RetrievalScope
from app.rag.filters import document_scope_filters, scope_has_embeddings
from app.rag.intent import is_profile_query, resolve_profile_document_ids
from app.rag.types import ChunkHit, DocumentSummary
from app.vectorstore.chunk_store import ChunkVectorStore

# 兼容旧 import
__all__ = [
	'ChunkHit',
	'DocumentSummary',
	'search_chunks',
	'search_chunks_dense',
	'search_chunks_sparse',
	'list_documents_for_scope',
	'format_rag_context',
	'hits_to_citations',
	'format_document_list',
	'merge_hybrid_hits',
]


def _query_terms(query: str) -> list[str]:
	text = query.strip()
	if not text:
		return []
	terms = [text]
	for part in text.replace('，', ' ').replace('。', ' ').split():
		part = part.strip()
		if len(part) >= 2 and part not in terms:
			terms.append(part)
	return terms[:6]


def merge_hybrid_hits(
	dense_hits: list[ChunkHit],
	sparse_hits: list[ChunkHit],
	*,
	limit: int,
	rrf_k: int | None = None,
) -> list[ChunkHit]:
	"""RRF 融合两路排序结果。"""
	k = rrf_k if rrf_k is not None else get_settings().retrieval_rrf_k
	scores: dict[uuid.UUID, float] = {}
	payload: dict[uuid.UUID, ChunkHit] = {}

	for rank, hit in enumerate(dense_hits):
		scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + rank + 1)
		payload[hit.chunk_id] = hit

	for rank, hit in enumerate(sparse_hits):
		scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + rank + 1)
		payload[hit.chunk_id] = hit

	ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
	out: list[ChunkHit] = []
	for chunk_id, rrf_score in ordered[:limit]:
		base = payload[chunk_id]
		out.append(
			ChunkHit(
				chunk_id=base.chunk_id,
				document_id=base.document_id,
				document_title=base.document_title,
				owner_type=base.owner_type,
				content=base.content,
				score=rrf_score,
				metadata=base.metadata,
			)
		)
	return out


def search_chunks_dense(
	session: Session,
	query: str,
	*,
	scope: RetrievalScope,
	user_id: uuid.UUID | None = None,
	limit: int | None = None,
	document_ids: list[uuid.UUID] | None = None,
) -> list[ChunkHit]:
	"""密集向量检索（pgvector）。"""
	settings = get_settings()
	k = limit if limit is not None else settings.retrieval_dense_top_k
	store = ChunkVectorStore(session)
	return store.similarity_search(
		query,
		scope=scope,
		user_id=user_id,
		k=k,
		document_ids=document_ids,
	)


def search_chunks_sparse(
	session: Session,
	query: str,
	*,
	scope: RetrievalScope,
	user_id: uuid.UUID | None = None,
	limit: int | None = None,
	document_ids: list[uuid.UUID] | None = None,
) -> list[ChunkHit]:
	"""稀疏关键词检索（正文 + 文档标题/文件名）。"""
	settings = get_settings()
	limit = limit if limit is not None else settings.retrieval_sparse_top_k
	terms = _query_terms(query)
	if not terms:
		return []

	filters = list(document_scope_filters(scope, user_id, ready_only=True))
	if document_ids:
		filters.append(Chunk.document_id.in_(document_ids))  # type: ignore[attr-defined]

	rows = session.exec(
		select(Chunk, Document)
		.join(Document, Chunk.document_id == Document.id)
		.where(*filters)
	).all()

	scored: list[ChunkHit] = []
	lower_terms = [t.lower() for t in terms]

	for chunk, doc in rows:
		body = chunk.content.lower()
		meta = f'{doc.title} {doc.original_filename or ""}'.lower()
		hits = sum(1 for t in lower_terms if t in body or t in meta)
		if hits == 0:
			continue
		score = hits / len(lower_terms)
		if terms[0].lower() in body:
			score += 0.5
		if any(t in meta for t in lower_terms):
			score += 0.8
		scored.append(
			ChunkHit(
				chunk_id=chunk.id,
				document_id=doc.id,
				document_title=doc.title,
				owner_type=doc.owner_type,
				content=chunk.content,
				score=score,
				metadata=chunk.chunk_metadata,
			)
		)

	scored.sort(key=lambda h: h.score, reverse=True)
	return scored[:limit]


def search_chunks_in_documents(
	session: Session,
	query: str,
	*,
	document_ids: list[uuid.UUID],
	scope: RetrievalScope,
	user_id: uuid.UUID | None = None,
	limit: int = 12,
) -> list[ChunkHit]:
	"""在指定文档内做混合检索；若仍无命中则返回该文档下全部 chunk（简历类兜底）。"""
	if not document_ids:
		return []

	sparse = search_chunks_sparse(
		session,
		query,
		scope=scope,
		user_id=user_id,
		limit=limit,
		document_ids=document_ids,
	)
	dense: list[ChunkHit] = []
	if scope_has_embeddings(session, scope, user_id):
		try:
			dense = search_chunks_dense(
				session,
				query,
				scope=scope,
				user_id=user_id,
				limit=limit,
				document_ids=document_ids,
			)
		except Exception:
			dense = []

	if dense or sparse:
		if dense and sparse:
			return merge_hybrid_hits(dense, sparse, limit=limit)
		return (dense or sparse)[:limit]

	# 兜底：用户问「项目/技术栈」但正文无关键词 → 仍返回简历文档分片
	filters = list(document_scope_filters(scope, user_id, ready_only=True))
	filters.append(Chunk.document_id.in_(document_ids))  # type: ignore[attr-defined]
	rows = session.exec(
		select(Chunk, Document)
		.join(Document, Chunk.document_id == Document.id)
		.where(*filters)
		.order_by(Chunk.created_at)  # type: ignore[attr-defined]
	).all()
	fallback: list[ChunkHit] = []
	for chunk, doc in rows[:limit]:
		fallback.append(
			ChunkHit(
				chunk_id=chunk.id,
				document_id=doc.id,
				document_title=doc.title,
				owner_type=doc.owner_type,
				content=chunk.content,
				score=0.1,
				metadata=chunk.chunk_metadata,
			)
		)
	return fallback


def search_chunks(
	session: Session,
	query: str,
	*,
	scope: RetrievalScope,
	user_id: uuid.UUID | None = None,
	limit: int | None = None,
) -> list[ChunkHit]:
	"""
	混合检索入口：密集 + 稀疏 → RRF → Top-K。

	若 scope 内尚无 embedding，则仅走稀疏路。
	若问题涉及简历/项目/技术栈，优先在「简历类」文档内检索。
	"""
	settings = get_settings()
	final_k = limit if limit is not None else settings.retrieval_final_top_k

	if is_profile_query(query):
		docs = list_documents_for_scope(session, scope=scope, user_id=user_id)
		profile_ids = resolve_profile_document_ids(docs)
		if profile_ids:
			profile_hits = search_chunks_in_documents(
				session,
				query,
				document_ids=profile_ids,
				scope=scope,
				user_id=user_id,
				limit=max(final_k, 10),
			)
			if profile_hits:
				return profile_hits[:final_k]

	sparse_hits = search_chunks_sparse(
		session, query, scope=scope, user_id=user_id
	)

	dense_hits: list[ChunkHit] = []
	if scope_has_embeddings(session, scope, user_id):
		try:
			dense_hits = search_chunks_dense(
				session, query, scope=scope, user_id=user_id
			)
		except Exception:
			# API Key 未配或向量化失败时降级稀疏
			dense_hits = []

	if dense_hits and sparse_hits:
		return merge_hybrid_hits(dense_hits, sparse_hits, limit=final_k)
	if dense_hits:
		return dense_hits[:final_k]
	return sparse_hits[:final_k]


def list_documents_for_scope(
	session: Session,
	*,
	scope: RetrievalScope,
	user_id: uuid.UUID | None = None,
	limit: int = 50,
) -> list[DocumentSummary]:
	try:
		filters = document_scope_filters(scope, user_id, ready_only=False)
	except ValueError:
		return []

	rows = session.exec(
		select(Document)
		.where(*filters)
		.order_by(Document.created_at.desc())  # type: ignore[attr-defined]
		.limit(limit)
	).all()

	return [
		DocumentSummary(
			id=row.id,
			title=row.title,
			owner_type=row.owner_type,
			status=row.status,
			chunk_count=row.chunk_count,
			original_filename=row.original_filename,
		)
		for row in rows
	]


def format_rag_context(hits: list[ChunkHit]) -> str:
	if not hits:
		return ''
	parts: list[str] = []
	for i, hit in enumerate(hits, 1):
		source = '系统教材' if hit.owner_type == OwnerType.system else '我的上传'
		parts.append(
			f'[{i}] 《{hit.document_title}》（{source}）\n{hit.content[:900]}'
		)
	return '\n\n'.join(parts)


def hits_to_citations(hits: list[ChunkHit]) -> list[dict[str, str]]:
	out: list[dict[str, str]] = []
	for hit in hits:
		source = '系统教材' if hit.owner_type == OwnerType.system else '我的上传'
		excerpt = hit.content.strip()
		if len(excerpt) > 320:
			excerpt = excerpt[:320] + '…'
		out.append(
			{
				'id': str(hit.chunk_id),
				'label': f'{hit.document_title} · {source}',
				'excerpt': excerpt,
			}
		)
	return out


def format_document_list(docs: list[DocumentSummary]) -> str:
	if not docs:
		return '当前检索范围内暂无文档。'
	lines: list[str] = []
	for doc in docs:
		source = '系统教材' if doc.owner_type == OwnerType.system else '我的上传'
		name = doc.original_filename or doc.title
		lines.append(
			f'- {doc.title}（{name}，{source}，状态 {doc.status.value}，{doc.chunk_count} 段）'
		)
	return '\n'.join(lines)
