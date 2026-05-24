"""Agent 可调用的知识库工具（scope 由会话上下文绑定）。"""

from __future__ import annotations

import uuid

from langchain.tools import tool
from sqlmodel import Session

from app.models.enums import RetrievalScope
from app.services.retrieval_service import (
	format_document_list,
	list_documents_for_scope,
	search_chunks,
)


def build_knowledge_tools(
	session: Session,
	*,
	scope: RetrievalScope,
	user_id: uuid.UUID | None,
) -> list:
	scope_label = {
		RetrievalScope.all: '全部（系统教材 + 我的上传）',
		RetrievalScope.system_only: '教材（系统预置）',
		RetrievalScope.user_only: '我的上传',
	}[scope]

	@tool
	def search_knowledge(query: str) -> str:
		"""混合检索知识库（向量 + 关键词 + RRF）。医学、简历、项目经历等问题均应调用。"""
		hits = search_chunks(
			session,
			query,
			scope=scope,
			user_id=user_id,
			limit=6,
		)
		if not hits:
			return f'在「{scope_label}」范围内未检索到与「{query}」相关的内容。'
		parts: list[str] = []
		for i, hit in enumerate(hits, 1):
			source = '系统教材' if hit.owner_type.value == 'system' else '我的上传'
			parts.append(
				f'[{i}] 《{hit.document_title}》（{source}）\n{hit.content[:800]}'
			)
		return '\n\n'.join(parts)

	@tool
	def list_knowledge_documents() -> str:
		"""列出当前检索范围内的知识库文档（标题、状态、分片数）。用户问有哪些文件/资料时调用。"""
		docs = list_documents_for_scope(session, scope=scope, user_id=user_id)
		header = f'当前范围：{scope_label}\n'
		return header + format_document_list(docs)

	return [search_knowledge, list_knowledge_documents]
