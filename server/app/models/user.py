"""
用户表 users — 以后登录、注册、JWT 都会读写这张表。

和「登录表单」的关系：
  - 表单里的邮箱 → email
  - 昵称 → display_name
  - 密码哈希以后可加字段 password_hash（当前 MVP 未建）
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
	# 对应数据库表名
	__tablename__ = 'users'

	# 主键，自动生成 UUID，全局唯一
	id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

	# 登录邮箱，可选；unique=True 表示不能重复注册
	email: str | None = Field(default=None, max_length=255, unique=True, index=True)

	# 显示名称，例如「张同学」
	display_name: str | None = Field(default=None, max_length=128)

	# 注册时间，由数据库默认 now()
	created_at: datetime = Field(
		sa_column=Column(
			DateTime(timezone=True),
			server_default=func.now(),
			nullable=False,
		),
	)

	# 资料更新时间
	updated_at: datetime = Field(
		sa_column=Column(
			DateTime(timezone=True),
			server_default=func.now(),
			onupdate=func.now(),
			nullable=False,
		),
		default_factory=lambda: datetime.now(timezone.utc),
	)
