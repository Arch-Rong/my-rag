"""
混合检索（Hybrid RAG）服务 — 聊天 / Agent 查资料的核心。

聊天主流程（agent.py）：
  1. search_chunks_vector()：仅向量检索
  2. 有命中 → 注入参考资料 + 用户问题 → 模型
  3. 无命中 → 仅用户问题 → 模型

工具 search_knowledge 仍走 search_chunks()（稀疏 + 密集 + RRF）。
"""

from __future__ import annotations  # 允许类型注解里写尚未定义的类型名

import uuid  # chunk_id、document_id、user_id 的类型

from sqlmodel import Session, select  # ORM：数据库会话 + 构造 SELECT 查询

from app.config import get_settings  # 读取 Top-K、RRF 常数等配置
from app.models.chunk import Chunk  # chunks 表：分片正文 + embedding
from app.models.document import Document  # documents 表：标题、文件名、scope 归属
from app.models.enums import OwnerType, RetrievalScope  # 系统教材 vs 用户上传；全部/教材/我的
from app.rag.filters import document_scope_filters, scope_has_embeddings  # 按聊天 scope 过滤文档；判断是否有向量
from app.rag.types import ChunkHit, DocumentSummary  # 检索命中结构；文档列表摘要
from app.vectorstore.chunk_store import ChunkVectorStore  # pgvector 密集检索封装

# 对外 re-export，其它模块可 from app.services.retrieval_service import search_chunks
__all__ = [
	'ChunkHit',
	'DocumentSummary',
	'search_chunks',
	'search_chunks_vector',
	'search_chunks_dense',
	'search_chunks_sparse',
	'list_documents_for_scope',
	'format_rag_context',
	'hits_to_citations',
	'format_document_list',
	'merge_hybrid_hits',
	'diversify_hits',
]


def _query_terms(query: str) -> list[str]:
	"""
	把用户问题拆成若干检索词（稀疏路用）。

	例：「心力衰竭怎么治疗」→ 整句 + 「心力衰竭」「怎么」「治疗」等（≥2 字才加入）
	最多 6 个词，避免拆太碎。
	"""
	text = query.strip()  # 去掉首尾空白
	if not text:  # 空问题无法检索
		return []
	terms = [text]  # 第一项永远是整句（提高整句匹配权重）
	for part in text.replace('，', ' ').replace('。', ' ').split():  # 按空格/中文标点分词
		part = part.strip()
		if len(part) >= 2 and part not in terms:  # 单字词噪声大，跳过重复
			terms.append(part)
	return terms[:6]  # 上限 6 个词


def merge_hybrid_hits(
	dense_hits: list[ChunkHit],  # 密集路 Top 列表（按向量相似度排好）
	sparse_hits: list[ChunkHit],  # 稀疏路 Top 列表（按关键词分数排好）
	*,
	limit: int,  # 最终要几条 chunk
	rrf_k: int | None = None,  # RRF 平滑常数，默认读配置 retrieval_rrf_k=60
) -> list[ChunkHit]:
	"""
	RRF（Reciprocal Rank Fusion）融合两路结果。

	同一 chunk 在两路都靠前 → 分数累加更高。
	公式：每路贡献 score += 1 / (k + rank + 1)，rank 从 0 开始。
	不直接比「向量分」和「关键词分」的绝对值（量纲不同），只比排名。
	"""
	k = rrf_k if rrf_k is not None else get_settings().retrieval_rrf_k
	scores: dict[uuid.UUID, float] = {}  # chunk_id → 累计 RRF 分
	payload: dict[uuid.UUID, ChunkHit] = {}  # chunk_id → 完整 ChunkHit（取正文用）

	for rank, hit in enumerate(dense_hits):  # 遍历密集路排名
		scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + rank + 1)
		payload[hit.chunk_id] = hit  # 保留 chunk 内容与元数据

	for rank, hit in enumerate(sparse_hits):  # 遍历稀疏路排名
		scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + rank + 1)
		payload[hit.chunk_id] = hit  # 若某 chunk 只出现在稀疏路，也会进 payload

	ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)  # 按 RRF 分降序
	out: list[ChunkHit] = []
	for chunk_id, rrf_score in ordered[:limit]:  # 取 Top limit
		base = payload[chunk_id]
		out.append(
			ChunkHit(
				chunk_id=base.chunk_id,
				document_id=base.document_id,
				document_title=base.document_title,
				owner_type=base.owner_type,
				content=base.content,
				score=rrf_score,  # 对外展示的 score 换成 RRF 分（供检索门控等使用）
				metadata=base.metadata,
			)
		)
	return out


def diversify_hits(
	hits: list[ChunkHit],
	limit: int,
	*,
	max_per_document: int | None = None,
) -> list[ChunkHit]:
	"""
	限制同一文档在结果里出现的条数，让多份资料（含用户上传）都有机会进 Top-K。

	按原分数顺序扫描，单文档已满 cap 条则跳过，直到凑满 limit 或候选用尽。
	"""
	if not hits or limit <= 0:
		return []
	cap = (
		max_per_document
		if max_per_document is not None
		else get_settings().retrieval_max_chunks_per_document
	)
	out: list[ChunkHit] = []
	per_doc: dict[uuid.UUID, int] = {}

	for hit in hits:
		if len(out) >= limit:
			break
		n = per_doc.get(hit.document_id, 0)
		if n >= cap:
			continue
		out.append(hit)
		per_doc[hit.document_id] = n + 1

	return out


def _finalize_hits(hits: list[ChunkHit], final_k: int) -> list[ChunkHit]:
	"""混合检索后的统一出口：按文档限流后截断到 final_k。"""
	return diversify_hits(hits, final_k)


def search_chunks_dense(
	session: Session,
	query: str,  # 用户自然语言问题
	*,
	scope: RetrievalScope,  # all / system_only / user_only（对应前端三个 Tab）
	user_id: uuid.UUID | None = None,  # 当前登录用户；user_only 和 all 时需要
	limit: int | None = None,  # 取几条，默认 retrieval_dense_top_k=12
	document_ids: list[uuid.UUID] | None = None,  # 非空时只在指定文档内搜
) -> list[ChunkHit]:
	"""
	路 A：密集向量检索。

	内部：embed_query(query) → ChunkVectorStore.similarity_search → pgvector 余弦距离。
	只查 embedding 非空的 chunk，且文档 status=ready。
	"""
	settings = get_settings()
	k = limit if limit is not None else settings.retrieval_dense_top_k
	store = ChunkVectorStore(session)  # 封装 pgvector 查询
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
	limit: int | None = None,  # 默认 retrieval_sparse_top_k=12
	document_ids: list[uuid.UUID] | None = None,
) -> list[ChunkHit]:
	"""
	路 B：稀疏关键词检索（简化 BM25，无倒排索引，扫 scope 内所有 chunk）。

	匹配位置：chunk.content + 文档 title + original_filename。
	适合专有名词、章节号等向量不一定准的场景。
	"""
	settings = get_settings()
	limit = limit if limit is not None else settings.retrieval_sparse_top_k
	terms = _query_terms(query)  # 拆词
	if not terms:
		return []  # 无词可搜

	# 组装 WHERE：未删除、ready、scope（教材/我的/全部）
	filters = list(document_scope_filters(scope, user_id, ready_only=True))
	if document_ids:
		filters.append(Chunk.document_id.in_(document_ids))  # type: ignore[attr-defined]

	# 拉出 scope 内所有 chunk，并 JOIN document 拿标题和文件名
	rows = session.exec(
		select(Chunk, Document)
		.join(Document, Chunk.document_id == Document.id)
		.where(*filters)
	).all()

	scored: list[ChunkHit] = []
	lower_terms = [t.lower() for t in terms]  # 不区分大小写匹配

	for chunk, doc in rows:
		body = chunk.content.lower()  # 分片正文
		meta = f'{doc.title} {doc.original_filename or ""}'.lower()  # 标题 + 文件名
		hits = sum(1 for t in lower_terms if t in body or t in meta)  # 命中了几个词
		if hits == 0:
			continue  # 一个词都没中，跳过
		score = hits / len(lower_terms)  # 基础分：命中率
		if terms[0].lower() in body:  # 整句出现在正文里，加分
			score += 0.5
		if any(t in meta for t in lower_terms):  # 词出现在文件名/标题，强加分（找「前端」「简历」）
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

	scored.sort(key=lambda h: h.score, reverse=True)  # 按关键词分从高到低
	return scored[:limit]


def search_chunks_vector(
	session: Session,  # 数据库会话，用于查 chunks / documents
	query: str,  # 用户在本轮聊天里输入的问题（自然语言）
	*,
	scope: RetrievalScope,  # 检索范围：all=全部 / system_only=教材 / user_only=我的上传
	user_id: uuid.UUID | None = None,  # 当前登录用户 ID；scope 为「我的」或「全部」且需区分用户时必传
	limit: int | None = None,  # 最终返回几条 chunk；默认读配置 retrieval_final_top_k（一般为 6）
) -> list[ChunkHit]:
	"""
	聊天主流程专用：只做向量检索，不做关键词（稀疏）检索。

	返回值非空 → agent.py 会把片段注入模型，并显示引用侧栏；
	返回 [] → 只把用户原问题交给模型，走通用对话。

	调用链：本函数 → search_chunks_dense → embed_query → pgvector。
	"""
	# 读取 .env / config.py 中的 Top-K、最低相似度等
	settings = get_settings()
	# 最终要给 LLM 的 chunk 条数（例如 6）
	final_k = limit if limit is not None else settings.retrieval_final_top_k

	# 当前 scope 下若没有任何 chunk 写过 embedding，向量检索无法进行，直接视为「未命中」
	if not scope_has_embeddings(session, scope, user_id):
		return []

	try:
		# 密集检索：问题先 embed_query，再与 chunks.embedding 做余弦相似度排序
		# limit 取 final_k * 3 作为候选池，后面会按分数过滤 + 每文档限流，再截回 final_k
		hits = search_chunks_dense(
			session,
			query,
			scope=scope,
			user_id=user_id,
			limit=final_k * 3,
		)
	except Exception:
		# Embedding API 失败、网络错误等：不抛给前端，当作没检索到，走纯聊天
		return []

	# 相似度下限（score = 1 - 余弦距离），低于此认为「蹭相似」不算真正命中
	min_score = settings.retrieval_vector_min_score
	# 过滤掉过弱的匹配，避免无关问题（如天气）仍注入医学教材片段
	filtered = [h for h in hits if h.score >= min_score]
	# 同一文档最多 N 条（默认 2），再取 Top final_k，避免一本大书占满 6 条
	return _finalize_hits(filtered, final_k)


def search_chunks(
	session: Session,
	query: str,
	*,
	scope: RetrievalScope,
	user_id: uuid.UUID | None = None,
	limit: int | None = None,
) -> list[ChunkHit]:
	"""
	混合检索总入口 — agent.py 预检索、search_knowledge 工具都会调这里。

	默认返回 retrieval_final_top_k=6 条 chunk。
	用户上传与系统教材走同一套混合检索，由 scope 控制范围；结果按文档限流避免单书占满。
	"""
	settings = get_settings()
	final_k = limit if limit is not None else settings.retrieval_final_top_k
	pool_k = max(final_k * 3, final_k)

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
			dense_hits = []  # 无 API Key 或向量化失败 → 仅稀疏

	if dense_hits and sparse_hits:
		merged = merge_hybrid_hits(dense_hits, sparse_hits, limit=pool_k)
		return _finalize_hits(merged, final_k)
	if dense_hits:
		return _finalize_hits(dense_hits, final_k)
	return _finalize_hits(sparse_hits, final_k)


def list_documents_for_scope(
	session: Session,
	*,
	scope: RetrievalScope,
	user_id: uuid.UUID | None = None,
	limit: int = 50,
) -> list[DocumentSummary]:
	"""
	列出当前 scope 下的文档元数据（不查 chunk 正文）。

	用于：简历路由前枚举文档、Agent 工具 list_knowledge_documents、
	格式化「知识库有哪些文件」的回答。
	"""
	try:
		filters = document_scope_filters(scope, user_id, ready_only=False)  # 含 queued/parsing 等状态
	except ValueError:
		return []  # 例如 user_only 但未登录

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
	"""
	把 Top-K chunk 拼成一段文本，注入给 LLM（agent.py 的 rag_context）。

	每条最多 900 字，带序号和书名，方便模型引用 [1][2]。
	"""
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
	"""
	转成前端引用侧栏 JSON：id（chunk_id）、label、excerpt。

	同一 PDF 多段引用时 id 不同，避免 React key 重复。
	"""
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
	"""把文档列表格式化成 Markdown 风格纯文本，给 Agent 工具返回用。"""
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
