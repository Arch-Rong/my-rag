"""检索结果按文档限流。"""

import uuid

from app.models.enums import OwnerType
from app.rag.types import ChunkHit
from app.services.retrieval_service import diversify_hits


def _hit(doc_id: uuid.UUID, score: float, n: int) -> ChunkHit:
	return ChunkHit(
		chunk_id=uuid.uuid4(),
		document_id=doc_id,
		document_title=f'doc-{n}',
		owner_type=OwnerType.user,
		content=f'chunk {n}',
		score=score,
		metadata=None,
	)


def test_diversify_limits_per_document() -> None:
	doc_a = uuid.uuid4()
	doc_b = uuid.uuid4()
	hits = [
		_hit(doc_a, 1.0, 1),
		_hit(doc_a, 0.9, 2),
		_hit(doc_a, 0.8, 3),
		_hit(doc_b, 0.7, 4),
	]
	out = diversify_hits(hits, limit=4, max_per_document=2)
	assert len(out) == 3
	assert sum(1 for h in out if h.document_id == doc_a) == 2
	assert sum(1 for h in out if h.document_id == doc_b) == 1
