"""检索门控单元测试。"""

import uuid

from app.models.enums import DocumentStatus, OwnerType
from app.rag.gate import is_kb_intent, max_gate_relevance, should_activate_rag
from app.rag.types import ChunkHit


def _hit(score: float) -> ChunkHit:
	return ChunkHit(
		chunk_id=uuid.uuid4(),
		document_id=uuid.uuid4(),
		document_title='测试',
		owner_type=OwnerType.system,
		content='心力衰竭诊疗',
		score=score,
		metadata=None,
	)


def test_kb_intent_profile_and_explicit() -> None:
	assert is_kb_intent('根据我的简历有哪些项目')
	assert is_kb_intent('知识库里有哪些文件')
	assert not is_kb_intent('今天天气怎么样')


def test_gate_off_for_chitchat_weak_hits() -> None:
	# 弱 RRF 分、非 kb_intent
	assert not should_activate_rag('今天天气怎么样', [_hit(0.016)])
	assert not should_activate_rag('FastAPI 是什么', [])


def test_gate_on_for_strong_dense_or_sparse() -> None:
	assert should_activate_rag('心力衰竭怎么治疗', [_hit(0.42)])


def test_gate_on_for_hybrid_rrf() -> None:
	# 双路 RRF Top1 约 0.032 → 映射后 0.32
	assert should_activate_rag('心力衰竭', [_hit(0.032)])


def test_kb_intent_without_hits_still_on() -> None:
	assert should_activate_rag('知识库里有没有 FastAPI', [])


def test_max_gate_relevance_scales_rrf() -> None:
	assert max_gate_relevance([_hit(0.016)]) == 0.16
	assert max_gate_relevance([_hit(0.5)]) == 0.5
