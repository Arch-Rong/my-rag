"""
数据库表模型（SQLModel）统一出口。

目录分工：
  enums.py      — 下拉框/状态机用的固定选项（如「教材」「已就绪」）
  constants.py  — 全项目共用的数字常量（如向量维度 1024）
  user.py       — 用户表（登录账号，以后接 JWT）
  document.py   — 知识库「一份文件」的元数据（PDF/MD 上传记录）
  chunk.py      — 把文档切成的小段 + 向量（RAG 检索真正查的是它）

关系（一张 Postgres 库 medrag 里）：
  User 1 ──< Document 多份文档
  Document 1 ──< Chunk 多个分块（每块可有 embedding 向量）
"""

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.enums import DocumentStatus, OwnerType, SourceType
from app.models.user import User

__all__ = [
	'User',
	'Document',
	'Chunk',
	'OwnerType',
	'SourceType',
	'DocumentStatus',
]
