"""
Postgres + pgvector 密集检索（LangChain VectorStore 的存储层等价实现）。

对应 RAG 流程中的「路 A」：
  用户问题 → embed_query → pgvector 余弦距离 → 取最相近的 K 条 chunk。
"""

from __future__ import annotations  # 允许类型注解里写 ChunkHit 等「前向引用」

import uuid  # user_id、chunk_id 的类型

from sqlmodel import Session, select  # ORM 会话 + SQL 查询构造

from app.embeddings.client import embed_query  # 把用户问题变成向量（调用方舟 Embedding API）
from app.models.chunk import Chunk  # chunks 表：分片正文 + embedding 列
from app.models.document import Document  # documents 表：用于 scope 过滤（教材/我的）
from app.models.enums import RetrievalScope  # all / system_only / user_only
from app.rag.filters import document_scope_filters  # 按聊天页「全部/教材/我的」拼 WHERE 条件
from app.rag.types import ChunkHit  # 检索结果统一结构（给混合检索、引用侧栏用）


class ChunkVectorStore:
	"""
	Chunk 向量库封装。

	不单独建 Milvus/Pinecone，直接用 Postgres 的 pgvector 扩展；
	语义上等同 LangChain 的 VectorStore.similarity_search。
	"""

	def __init__(self, session: Session) -> None:
		# 持有数据库会话，查询 chunks 并 JOIN documents
		self._session = session

	def similarity_search(
		self,
		query: str,  # 用户自然语言问题，如「心力衰竭怎么治疗」
		*,
		scope: RetrievalScope,  # 检索范围：全部 / 仅教材 / 仅我的上传
		user_id: uuid.UUID | None = None,  # 当前登录用户；user_only / all 时需要
		k: int = 12,  # 密集路先取多少条（后续 RRF 可能再筛到 6 条）
		document_ids: list[uuid.UUID] | None = None,  # 限定在若干文档内检索（如简历 PDF）
	) -> list[ChunkHit]:
		# ① 问题 → 向量（与入库时 chunk.embedding 同一模型、同一维度）
		query_vector = embed_query(query)

		# ② 根据 scope 生成 SQL 过滤：未删、ready、owner_type / user_id
		filters = list(document_scope_filters(scope, user_id, ready_only=True))
		if document_ids:
			filters.append(Chunk.document_id.in_(document_ids))  # type: ignore[attr-defined]

		# ③ pgvector：计算每行 chunk.embedding 与 query_vector 的余弦距离（越小越相似）
		distance_expr = Chunk.embedding.cosine_distance(query_vector)

		# ④ 执行查询：chunk 关联 document，只查已有向量的行，按距离升序，取 Top-K
		rows = self._session.exec(
			select(Chunk, Document, distance_expr.label('distance'))
			.join(Document, Chunk.document_id == Document.id)
			.where(*filters, Chunk.embedding.isnot(None))  # type: ignore[union-attr]
			.order_by(distance_expr)  # 距离最小 = 最相似
			.limit(k)
		).all()

		# ⑤ 把数据库行转成 ChunkHit，并做距离 → 相似度分数
		hits: list[ChunkHit] = []
		for chunk, doc, distance in rows:
			dist = float(distance) if distance is not None else 2.0  # 余弦距离，范围约 [0, 2]
			score = max(0.0, 1.0 - dist)  # 转成「越大越相似」的分数，便于和稀疏路 RRF 融合
			hits.append(
				ChunkHit(
					chunk_id=chunk.id,
					document_id=doc.id,
					document_title=doc.title,  # 引用侧栏显示书名/标题
					owner_type=doc.owner_type,  # system=教材，user=我的上传
					content=chunk.content,  # 分片正文，会喂给 LLM
					score=score,
					metadata=chunk.chunk_metadata,  # 页码、章节等 JSON
				)
			)
		return hits  # 交给 retrieval_service 与稀疏结果做 RRF 合并
