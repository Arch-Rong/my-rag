"""
火山方舟多模态向量化 API（/embeddings/multimodal）。

模型如 doubao-embedding-vision-251215 不能使用 OpenAI 标准 /embeddings，
也勿用 LangChain OpenAIEmbeddings（会把 input 变成 token id 数组导致 400）。
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# 入库分片：与控制台示例类似，仅文本模态
DEFAULT_DOC_INSTRUCTIONS = (
	'Target_modality: text.\n'
	'Instruction:Represent the document for retrieval.\n'
	'Query:'
)

# 检索问题
DEFAULT_QUERY_INSTRUCTIONS = (
	'Target_modality: text.\n'
	'Instruction:Represent the query for retrieval.\n'
	'Query:'
)


def is_multimodal_embedding_model(model: str) -> bool:
	name = model.lower()
	return 'vision' in name or 'multimodal' in name


def _multimodal_url() -> str:
	base = get_settings().llm_api_base.rstrip('/')
	return f'{base}/embeddings/multimodal'


def _parse_embedding_response(payload: dict[str, Any]) -> list[float]:
	"""兼容方舟多模态返回：data.embedding 或 data[].embedding。"""
	data = payload.get('data')
	if isinstance(data, dict):
		emb = data.get('embedding')
		if isinstance(emb, list):
			if emb and isinstance(emb[0], (int, float)):
				return [float(x) for x in emb]
			if emb and isinstance(emb[0], list):
				return [float(x) for x in emb[0]]
	if isinstance(data, list) and data:
		first = data[0]
		if isinstance(first, dict) and 'embedding' in first:
			emb = first['embedding']
			return [float(x) for x in emb]
	# OpenAI 兼容 list 形态
	if isinstance(data, list):
		for item in data:
			if isinstance(item, dict) and item.get('object') == 'embedding':
				return [float(x) for x in item['embedding']]
	raise ValueError(
		f'unexpected multimodal embedding response keys: {list(payload.keys())}'
	)


def _call_multimodal(
	text: str,
	*,
	instructions: str,
) -> list[float]:
	settings = get_settings()
	if not settings.llm_api_key.strip():
		raise RuntimeError('ARK_API_KEY not configured for embeddings')

	body: dict[str, Any] = {
		'model': settings.embedding_model,
		'instructions': instructions,
		'input': [{'type': 'text', 'text': text.strip()[:12000]}],
		'dimensions': settings.embedding_dim,
		'encoding_format': 'float',
	}
	# 与控制台示例一致；检索仅用 dense 向量，可不启 sparse
	if settings.embedding_multimodal_sparse:
		body['sparse_embedding'] = {'type': 'enabled'}
	else:
		body['sparse_embedding'] = {'type': 'disabled'}

	headers = {
		'Authorization': f'Bearer {settings.llm_api_key}',
		'Content-Type': 'application/json',
	}

	with httpx.Client(timeout=settings.embedding_request_timeout) as client:
		resp = client.post(_multimodal_url(), headers=headers, json=body)
		if resp.status_code >= 400:
			logger.error(
				'multimodal embedding HTTP %s: %s',
				resp.status_code,
				resp.text[:500],
			)
		resp.raise_for_status()
		return _parse_embedding_response(resp.json())


def embed_query_multimodal(text: str) -> list[float]:
	settings = get_settings()
	instructions = (
		settings.embedding_query_instructions or DEFAULT_QUERY_INSTRUCTIONS
	)
	return _call_multimodal(text, instructions=instructions)


def embed_documents_multimodal(texts: list[str]) -> list[list[float]]:
	if not texts:
		return []
	settings = get_settings()
	instructions = (
		settings.embedding_doc_instructions or DEFAULT_DOC_INSTRUCTIONS
	)
	# 方舟多模态接口按条请求最稳（避免 multi_embedding 响应格式差异）
	return [_call_multimodal(t, instructions=instructions) for t in texts]
