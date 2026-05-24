"""分片向量化：写入 chunks.embedding（pgvector）。"""

import logging
import uuid

from sqlmodel import Session, select

from app.config import get_settings
from app.embeddings.client import embed_documents
from app.models.chunk import Chunk

logger = logging.getLogger(__name__)


def embed_document_chunks(session: Session, document_id: uuid.UUID) -> int:
	"""
	为某文档下所有 chunk 生成 embedding 并落库。

	API 未配置或调用失败时抛错，由 ingest 捕获后仅记日志（仍可用稀疏检索）。
	"""
	settings = get_settings()
	if not settings.llm_api_key.strip():
		raise RuntimeError('ARK_API_KEY not configured for embeddings')

	chunks = list(
		session.exec(select(Chunk).where(Chunk.document_id == document_id)).all()
	)
	if not chunks:
		return 0

	texts = [c.content for c in chunks]
	vectors = embed_documents(texts)
	if len(vectors) != len(chunks):
		raise RuntimeError('embedding count mismatch')

	for chunk, vector in zip(chunks, vectors, strict=True):
		if len(vector) != settings.embedding_dim:
			raise RuntimeError(
				f'expected dim {settings.embedding_dim}, got {len(vector)}'
			)
		chunk.embedding = vector
		session.add(chunk)

	session.commit()
	logger.info('embedded %s chunks for document %s', len(chunks), document_id)
	return len(chunks)
