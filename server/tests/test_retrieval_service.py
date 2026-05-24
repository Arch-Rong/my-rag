"""RAG 检索 scope 过滤单元测试。"""

import uuid

import pytest
from sqlmodel import Session, create_engine

from app.models.document import Document
from app.models.enums import DocumentStatus, OwnerType, RetrievalScope, SourceType
from app.services.retrieval_service import list_documents_for_scope, search_chunks

pytestmark = pytest.mark.skipif(
	not __import__('os').getenv('DATABASE_URL'),
	reason='DATABASE_URL 未设置',
)


@pytest.fixture
def db_session() -> Session:
	engine = create_engine(__import__('os').environ['DATABASE_URL'], pool_pre_ping=True)
	with Session(engine) as session:
		yield session


def test_search_chunks_respects_user_scope(db_session: Session) -> None:
	user_id = uuid.uuid4()
	system_doc = Document(
		id=uuid.uuid4(),
		owner_type=OwnerType.system,
		title='系统内科学',
		source_type=SourceType.textbook,
		status=DocumentStatus.ready,
		chunk_count=1,
	)
	user_doc = Document(
		id=uuid.uuid4(),
		user_id=user_id,
		owner_type=OwnerType.user,
		title='我的笔记',
		source_type=SourceType.user_upload,
		status=DocumentStatus.ready,
		chunk_count=1,
	)
	db_session.add(system_doc)
	db_session.add(user_doc)
	db_session.commit()

	from app.models.chunk import Chunk

	db_session.add(
		Chunk(
			document_id=system_doc.id,
			content='心力衰竭的主要表现与诊疗要点',
		)
	)
	db_session.add(
		Chunk(
			document_id=user_doc.id,
			content='心力衰竭复习笔记期末重点',
		)
	)
	db_session.commit()

	system_hits = search_chunks(
		db_session,
		'心力衰竭',
		scope=RetrievalScope.system_only,
		user_id=user_id,
	)
	assert all(h.owner_type == OwnerType.system for h in system_hits)

	user_hits = search_chunks(
		db_session,
		'心力衰竭',
		scope=RetrievalScope.user_only,
		user_id=user_id,
	)
	assert all(h.owner_type == OwnerType.user for h in user_hits)

	all_hits = search_chunks(
		db_session,
		'心力衰竭',
		scope=RetrievalScope.all,
		user_id=user_id,
	)
	assert len(all_hits) >= 2

	# cleanup
	for row in db_session.exec(
		__import__('sqlmodel').select(Chunk).where(
			Chunk.document_id.in_([system_doc.id, user_doc.id])
		)
	).all():
		db_session.delete(row)
	db_session.delete(system_doc)
	db_session.delete(user_doc)
	db_session.commit()


def test_list_documents_user_only_requires_user(db_session: Session) -> None:
	assert list_documents_for_scope(
		db_session, scope=RetrievalScope.user_only, user_id=None
	) == []
