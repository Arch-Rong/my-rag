"""ingest：解析 + 分片写入 chunks（Postgres + 本地存储）。"""

import uuid
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, select

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.enums import DocumentStatus, OwnerType, SourceType
from app.models.user import User
from app.services.document_service import create_document_upload
from app.services.ingest_service import ingest_document
from app.storage.filesystem_storage import FilesystemObjectStorage

pytestmark = pytest.mark.skipif(
	not __import__('os').getenv('DATABASE_URL'),
	reason='DATABASE_URL 未设置',
)

SAMPLE_MD = b"""# Test Doc

## Section A

Hello from section A.

## Section B

Hello from section B.
"""


@pytest.fixture
def engine():
	return create_engine(__import__('os').environ['DATABASE_URL'], pool_pre_ping=True)


def test_ingest_markdown_creates_chunks(engine, tmp_path: Path) -> None:
	storage = FilesystemObjectStorage(tmp_path)
	user_id = uuid.uuid4()
	with Session(engine) as session:
		session.add(
			User(
				id=user_id,
				email=f'ingest-{user_id}@example.com',
				display_name='Ingest Test',
				password_hash='x',
			)
		)
		session.commit()

	with Session(engine) as session:
		doc = create_document_upload(
			session,
			storage,
			user_id=user_id,
			title='Test',
			filename='notes.md',
			data=SAMPLE_MD,
		)
		doc_id = doc.id

	with Session(engine) as session:
		result = ingest_document(session, storage, doc_id)
		assert result.status == DocumentStatus.ready
		assert result.chunk_count >= 2

	with Session(engine) as session:
		chunks = session.exec(select(Chunk).where(Chunk.document_id == doc_id)).all()
		assert len(chunks) == result.chunk_count
		assert any('section A' in c.content or 'Section A' in c.content for c in chunks)
		for c in chunks:
			assert c.chunk_metadata is not None
			assert 'chunk_index' in c.chunk_metadata
