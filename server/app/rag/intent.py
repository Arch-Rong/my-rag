"""用户问题 / 文档文件名 意图识别（简历 vs 医学教材等）。"""

from __future__ import annotations

import uuid

from app.models.enums import OwnerType
from app.rag.types import DocumentSummary

# 用户问题里出现这些词 → 按「个人资料/简历」处理
PROFILE_QUERY_KEYWORDS = (
	'简历',
	'履历',
	'cv',
	'resume',
	'工作经历',
	'工作项目',
	'项目经历',
	'项目经验',
	'技术栈',
	'擅长什么',
	'我的项目',
	'做过什么项目',
)

# 文件名/标题里出现这些 → 视为简历、作品集类（非医学教材）
PROFILE_DOC_KEYWORDS = (
	'简历',
	'resume',
	'cv',
	'履历',
	'前端',
	'后端',
	'工程师',
	'作品集',
	'portfolio',
)

# 文件名里出现这些 → 视为医学教材，简历类问题时应降权
MEDICAL_DOC_KEYWORDS = (
	'医学',
	'教材',
	'内科学',
	'外科学',
	'生理学',
	'病理',
	'药理',
	'临床',
	'生长发育',
	'解剖',
)


def is_profile_query(query: str) -> bool:
	q = query.lower()
	return any(kw in q for kw in PROFILE_QUERY_KEYWORDS)


def _doc_label(doc: DocumentSummary) -> str:
	return f'{doc.title} {doc.original_filename or ""}'.lower()


def is_profile_document(doc: DocumentSummary) -> bool:
	text = _doc_label(doc)
	if any(kw in text for kw in PROFILE_DOC_KEYWORDS):
		return True
	# 用户上传、文件名不像医学教材 → 可能是简历/笔记/报告
	if doc.owner_type == OwnerType.user and not any(
		kw in text for kw in MEDICAL_DOC_KEYWORDS
	):
		return True
	return False


def resolve_profile_document_ids(docs: list[DocumentSummary]) -> list[uuid.UUID]:
	"""从 scope 内文档中挑出最像简历/个人资料的文件。"""
	profile = [doc.id for doc in docs if is_profile_document(doc)]
	if profile:
		return profile
	# 兜底：用户上传且唯一非医学命名
	user_non_medical = [
		doc.id
		for doc in docs
		if doc.owner_type == OwnerType.user
		and not any(kw in _doc_label(doc) for kw in MEDICAL_DOC_KEYWORDS)
	]
	return user_non_medical
