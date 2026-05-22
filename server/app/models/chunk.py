"""
分块表 chunks — RAG 检索的核心。

一份 Document 会被切成多段文字，每段一行 Chunk：
  - content：这一段正文（模型读的内容）
  - chunk_metadata：章节、页码等（JSON，数据库列名 metadata）
  - embedding：这一段对应的向量（pgvector，存在同一 Postgres 库里）

问答时：用户问题 → 向量相似度搜 chunks → 把 Top-K 段 content 交给大模型。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

# pgvector 提供的列类型，不是单独的数据库
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.models.constants import DEFAULT_EMBEDDING_DIM

if TYPE_CHECKING:
	from app.models.document import Document


class Chunk(SQLModel, table=True):
	__tablename__ = 'chunks'

	# 按 document_id 查某本书的所有块时会用到
	__table_args__ = (Index('ix_chunks_document_id', 'document_id'),)

	id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

	# 属于哪份文档；删文档时级联删掉所有 chunk（ondelete=CASCADE）
	document_id: uuid.UUID = Field(
		sa_column=Column(
			ForeignKey('documents.id', ondelete='CASCADE'),
			nullable=False,
		),
	)

	# 这一块的纯文本（引用侧边栏展示的 excerpt 也来自这里）
	content: str = Field(sa_column=Column(Text, nullable=False))

	# 可选：估算 token 数，控制上下文长度
	token_count: int | None = Field(default=None)

	# 元数据：如 {"chapter": "第3章", "page": 128}
	# Python 属性叫 chunk_metadata，因为 metadata 在 SQLAlchemy 里是保留名
	chunk_metadata: dict[str, Any] | None = Field(
		default=None,
		sa_column=Column('metadata', JSONB, nullable=True),
	)

	# 向量；入库中可能先 NULL，embedding 完成后再 UPDATE
	# 长度 DEFAULT_EMBEDDING_DIM（1024），和 Embedding 模型输出一致
	embedding: list[float] | None = Field(
		default=None,
		sa_column=Column(Vector(DEFAULT_EMBEDDING_DIM), nullable=True),
	)

	created_at: datetime = Field(
		sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
	)

	# 反向关系：chunk.document 可回到所属 Document
	document: Optional['Document'] = Relationship(back_populates='chunks')
