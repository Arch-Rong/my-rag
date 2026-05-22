"""
文档表 documents — 知识库里「每一份文件」一条记录。

例如用户上传《内科学.pdf》：
  - 一行 Document：标题、大小、状态、存在磁盘哪、属于哪个用户
  - 解析后会拆成很多行 Chunk（见 chunk.py）

和前端「知识库列表」一一对应。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

# 仅类型检查用，避免和 Chunk 循环 import
if TYPE_CHECKING:
	from app.models.chunk import Chunk

from sqlalchemy import Column, DateTime, Enum, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import DocumentStatus, OwnerType, SourceType


class Document(SQLModel, table=True):
	__tablename__ = 'documents'

	id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

	# 上传者；系统预置教材则为 NULL
	user_id: uuid.UUID | None = Field(default=None, foreign_key='users.id', index=True)

	# 系统库 vs 用户库（对应聊天页「教材 / 我的」筛选）
	owner_type: OwnerType = Field(
		sa_column=Column(Enum(OwnerType, name='owner_type', native_enum=True), nullable=False),
	)

	# 列表里显示的名字（可改，不必等于文件名）
	title: str = Field(max_length=512)

	# 用户上传时的原始文件名
	original_filename: str | None = Field(default=None, max_length=512)

	# 教材 / 指南 / 讲义 / 用户上传
	source_type: SourceType = Field(
		default=SourceType.user_upload,
		sa_column=Column(Enum(SourceType, name='source_type', native_enum=True), nullable=False),
	)

	# 如 application/pdf
	mime_type: str | None = Field(default=None, max_length=128)

	# 文件字节大小
	file_size: int | None = Field(default=None)

	# 磁盘或对象存储上的路径（Worker 读这个路径去解析）
	file_path: str | None = Field(default=None, max_length=1024)

	# 文件内容哈希，用于去重、判断是否要重新入库
	content_hash: str | None = Field(default=None, max_length=128, index=True)

	# 冗余字段：有多少个 chunk，列表页展示用，不用每次 COUNT
	chunk_count: int = Field(default=0)

	# 入库状态：排队 → 解析 → 向量化 → 就绪 / 失败
	status: DocumentStatus = Field(
		sa_column=Column(
			Enum(DocumentStatus, name='document_status', native_enum=True),
			nullable=False,
			index=True,
		),
		default=DocumentStatus.queued,
	)

	# 失败时的错误信息（给人看）
	error_message: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

	# 用户自定义标签，JSON 如 {"学期":"期末","科室":"呼吸"}
	tags: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))

	created_at: datetime = Field(
		sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
	)

	updated_at: datetime = Field(
		sa_column=Column(
			DateTime(timezone=True),
			server_default=func.now(),
			onupdate=func.now(),
			nullable=False,
		),
	)

	# 软删除时间；有值则视为已删，检索必须过滤掉
	deleted_at: datetime | None = Field(
		default=None,
		sa_column=Column(DateTime(timezone=True), nullable=True),
	)

	# ORM 关系：一份文档下有很多 Chunk（代码里 document.chunks 可访问）
	chunks: list['Chunk'] = Relationship(back_populates='document')
