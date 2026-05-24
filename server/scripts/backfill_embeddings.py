#!/usr/bin/env python3
"""为已有 chunks 补写 embedding（需 ARK_API_KEY）。"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session, select

from app.db.session import engine
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.enums import DocumentStatus
from app.services.embedding_service import embed_document_chunks


def main() -> None:
	doc_id: uuid.UUID | None = None
	if len(sys.argv) > 1:
		doc_id = uuid.UUID(sys.argv[1])

	with Session(engine) as session:
		if doc_id:
			doc_ids = [doc_id]
		else:
			doc_ids = list(
				session.exec(
					select(Document.id).where(Document.status == DocumentStatus.ready)
				).all()
			)

		total = 0
		for did in doc_ids:
			missing = session.exec(
				select(Chunk.id).where(
					Chunk.document_id == did,
					Chunk.embedding.is_(None),  # type: ignore[union-attr]
				)
			).first()
			if missing is None:
				continue
			try:
				n = embed_document_chunks(session, did)
				total += n
				print(f'embedded {n} chunks for {did}')
			except Exception as exc:
				print(f'skip {did}: {exc}', file=sys.stderr)

		print(f'done, total chunks embedded: {total}')


if __name__ == '__main__':
	main()
