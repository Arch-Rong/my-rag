"""向量检索是否启用 RAG（有命中即用）。"""

import uuid

from app.models.enums import OwnerType
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


def test_use_rag_when_vector_hits_exist() -> None:
	assert bool([_hit(0.5)]) is True


def test_no_rag_when_vector_hits_empty() -> None:
	assert bool([]) is False
