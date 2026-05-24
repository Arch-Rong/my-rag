"""简历类问题意图与文档匹配。"""

import uuid

from app.models.enums import DocumentStatus, OwnerType
from app.rag.intent import is_profile_document, is_profile_query, resolve_profile_document_ids
from app.rag.types import DocumentSummary


def test_is_profile_query() -> None:
	assert is_profile_query('根据我的简历，工作项目有哪些')
	assert is_profile_query('我的技术栈是什么')
	assert not is_profile_query('心力衰竭怎么治疗')


def test_resolve_profile_document_ids_prefers_resume_filename() -> None:
	resume_id = uuid.uuid4()
	medical_id = uuid.uuid4()
	docs = [
		DocumentSummary(
			id=resume_id,
			title='荣文茹前端260313',
			owner_type=OwnerType.user,
			status=DocumentStatus.ready,
			chunk_count=5,
			original_filename='荣文茹前端260313.pdf',
		),
		DocumentSummary(
			id=medical_id,
			title='人类生长发育',
			owner_type=OwnerType.system,
			status=DocumentStatus.ready,
			chunk_count=20,
			original_filename='人类生长发育（医学完整版）.pdf',
		),
	]
	ids = resolve_profile_document_ids(docs)
	assert resume_id in ids
	assert medical_id not in ids


def test_is_profile_document_user_non_medical() -> None:
	doc = DocumentSummary(
		id=uuid.uuid4(),
		title='个人报告',
		owner_type=OwnerType.user,
		status=DocumentStatus.ready,
		chunk_count=1,
		original_filename='report.pdf',
	)
	assert is_profile_document(doc)
