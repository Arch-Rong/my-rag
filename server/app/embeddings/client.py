"""火山方舟 OpenAI 兼容 Embedding API。"""

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from app.config import get_settings


@lru_cache
def get_embedding_client() -> OpenAIEmbeddings:
	settings = get_settings()
	return OpenAIEmbeddings(
		model=settings.embedding_model,
		api_key=settings.llm_api_key or None,
		base_url=settings.llm_api_base,
		# 与 chunks.embedding 列维数、pgvector 迁移一致（火山方舟支持降维）
		dimensions=settings.embedding_dim,
	)


def embed_query(text: str) -> list[float]:
	"""单条问题向量化（检索 Query）。"""
	client = get_embedding_client()
	return client.embed_query(text.strip())


def embed_documents(texts: list[str]) -> list[list[float]]:
	"""批量文档分片向量化（入库）。"""
	if not texts:
		return []
	client = get_embedding_client()
	return client.embed_documents(texts)
