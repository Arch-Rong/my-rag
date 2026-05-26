"""火山方舟 Embedding：标准 /embeddings 与多模态 /embeddings/multimodal。"""

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from app.config import get_settings
from app.embeddings.volcengine_multimodal import (
	embed_documents_multimodal,
	embed_query_multimodal,
	is_multimodal_embedding_model,
)


@lru_cache
def get_embedding_client() -> OpenAIEmbeddings:
	"""仅用于非 vision 类文本向量模型（/embeddings）。"""
	settings = get_settings()
	return OpenAIEmbeddings(
		model=settings.embedding_model,
		api_key=settings.llm_api_key or None,
		base_url=settings.llm_api_base,
		dimensions=settings.embedding_dim,
	)


def embed_query(text: str) -> list[float]:
	"""单条问题向量化（检索 Query）。"""
	settings = get_settings()
	if is_multimodal_embedding_model(settings.embedding_model):
		return embed_query_multimodal(text)
	client = get_embedding_client()
	return client.embed_query(text.strip())


def embed_documents(texts: list[str]) -> list[list[float]]:
	"""批量文档分片向量化（入库）。"""
	if not texts:
		return []
	settings = get_settings()
	if is_multimodal_embedding_model(settings.embedding_model):
		return embed_documents_multimodal(texts)
	client = get_embedding_client()
	return client.embed_documents(texts)
