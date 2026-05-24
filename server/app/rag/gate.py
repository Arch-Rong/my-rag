"""检索门控：决定是否注入 RAG 上下文并启用知识库工具。"""

from __future__ import annotations

from app.config import get_settings
from app.rag.intent import is_profile_query
from app.rag.types import ChunkHit

# 用户明确在问知识库 / 教材 / 个人上传资料
KB_INTENT_KEYWORDS = (
	'知识库',
	'教材',
	'资料',
	'文献',
	'课本',
	'文档',
	'上传',
	'引用了',
	'出处',
	'根据',
	'检索',
	'有哪些文件',
	'有哪些资料',
	'列出文件',
	'列出资料',
	'我的上传',
	'系统教材',
)


def is_kb_intent(query: str) -> bool:
	"""用户是否在明确询问知识库内容（含简历/项目类）。"""
	if is_profile_query(query):
		return True
	q = query.lower()
	return any(kw in q for kw in KB_INTENT_KEYWORDS)


def _gate_relevance(score: float) -> float:
	"""
	将稀疏/密集分（常 ≥0.15）与 RRF 分（常 <0.06）映射到可比较的尺度。
	"""
	if score >= 0.15:
		return score
	return min(1.0, score * 10.0)


def max_gate_relevance(hits: list[ChunkHit]) -> float:
	if not hits:
		return 0.0
	return max(_gate_relevance(h.score) for h in hits)


def should_activate_rag(query: str, hits: list[ChunkHit]) -> bool:
	"""
	是否启用 RAG 模式（注入上下文 + 知识库工具 + 要求引用）。

	规则：kb_intent 或 max_relevance ≥ τ；否则走普通对话。
	"""
	if is_kb_intent(query):
		return True
	if not hits:
		return False
	tau = get_settings().retrieval_gate_score_threshold
	return max_gate_relevance(hits) >= tau
