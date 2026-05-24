"""混合检索 RRF 单元测试（不依赖数据库）。"""

import uuid

from app.models.enums import OwnerType
from app.rag.types import ChunkHit
from app.services.retrieval_service import merge_hybrid_hits


def _hit(chunk_id: uuid.UUID, score: float) -> ChunkHit:
	return ChunkHit(
		chunk_id=chunk_id,
		document_id=uuid.uuid4(),
		document_title='t',
		owner_type=OwnerType.system,
		content='body',
		score=score,
		metadata=None,
	)


def test_rrf_prefers_both_lists() -> None:
	a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
	dense = [_hit(a, 0.9), _hit(b, 0.8)]
	sparse = [_hit(b, 0.7), _hit(c, 0.6)]
	merged = merge_hybrid_hits(dense, sparse, limit=3, rrf_k=60)
	ids = [h.chunk_id for h in merged]
	assert b in ids
	assert len(merged) == 3
