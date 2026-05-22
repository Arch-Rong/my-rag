"""initial schema: users, documents, chunks + pgvector

Revision ID: 20260516_0001
Revises:
Create Date: 2026-05-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = '20260516_0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 1024

owner_type_enum = postgresql.ENUM(
	'system',
	'user',
	name='owner_type',
	create_type=False,
)
source_type_enum = postgresql.ENUM(
	'textbook',
	'guideline',
	'lecture',
	'user_upload',
	name='source_type',
	create_type=False,
)
document_status_enum = postgresql.ENUM(
	'queued',
	'parsing',
	'embedding',
	'ready',
	'failed',
	'deleted',
	name='document_status',
	create_type=False,
)


def upgrade() -> None:
	op.execute('CREATE EXTENSION IF NOT EXISTS vector')

	owner_type_enum.create(op.get_bind(), checkfirst=True)
	source_type_enum.create(op.get_bind(), checkfirst=True)
	document_status_enum.create(op.get_bind(), checkfirst=True)

	op.create_table(
		'users',
		sa.Column('id', sa.Uuid(), nullable=False),
		sa.Column('email', sa.String(length=255), nullable=True),
		sa.Column('display_name', sa.String(length=128), nullable=True),
		sa.Column(
			'created_at',
			sa.DateTime(timezone=True),
			server_default=sa.text('now()'),
			nullable=False,
		),
		sa.Column(
			'updated_at',
			sa.DateTime(timezone=True),
			server_default=sa.text('now()'),
			nullable=False,
		),
		sa.PrimaryKeyConstraint('id'),
	)
	op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

	op.create_table(
		'documents',
		sa.Column('id', sa.Uuid(), nullable=False),
		sa.Column('user_id', sa.Uuid(), nullable=True),
		sa.Column('owner_type', owner_type_enum, nullable=False),
		sa.Column('title', sa.String(length=512), nullable=False),
		sa.Column('original_filename', sa.String(length=512), nullable=True),
		sa.Column('source_type', source_type_enum, nullable=False),
		sa.Column('mime_type', sa.String(length=128), nullable=True),
		sa.Column('file_size', sa.BigInteger(), nullable=True),
		sa.Column('file_path', sa.String(length=1024), nullable=True),
		sa.Column('content_hash', sa.String(length=128), nullable=True),
		sa.Column('chunk_count', sa.Integer(), server_default='0', nullable=False),
		sa.Column('status', document_status_enum, nullable=False),
		sa.Column('error_message', sa.Text(), nullable=True),
		sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
		sa.Column(
			'created_at',
			sa.DateTime(timezone=True),
			server_default=sa.text('now()'),
			nullable=False,
		),
		sa.Column(
			'updated_at',
			sa.DateTime(timezone=True),
			server_default=sa.text('now()'),
			nullable=False,
		),
		sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
		sa.ForeignKeyConstraint(['user_id'], ['users.id']),
		sa.PrimaryKeyConstraint('id'),
	)
	op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)
	op.create_index(
		op.f('ix_documents_content_hash'), 'documents', ['content_hash'], unique=False
	)
	op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)

	op.create_table(
		'chunks',
		sa.Column('id', sa.Uuid(), nullable=False),
		sa.Column('document_id', sa.Uuid(), nullable=False),
		sa.Column('content', sa.Text(), nullable=False),
		sa.Column('token_count', sa.Integer(), nullable=True),
		sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
		sa.Column('embedding', Vector(EMBEDDING_DIM), nullable=True),
		sa.Column(
			'created_at',
			sa.DateTime(timezone=True),
			server_default=sa.text('now()'),
			nullable=False,
		),
		sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
		sa.PrimaryKeyConstraint('id'),
	)
	op.create_index('ix_chunks_document_id', 'chunks', ['document_id'], unique=False)

	# 向量相似度检索索引（表有数据后可建；空表创建亦无害）
	op.execute(
		"""
		CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw
		ON chunks USING hnsw (embedding vector_cosine_ops)
		"""
	)


def downgrade() -> None:
	op.execute('DROP INDEX IF EXISTS ix_chunks_embedding_hnsw')
	op.drop_index('ix_chunks_document_id', table_name='chunks')
	op.drop_table('chunks')
	op.drop_index(op.f('ix_documents_status'), table_name='documents')
	op.drop_index(op.f('ix_documents_content_hash'), table_name='documents')
	op.drop_index(op.f('ix_documents_user_id'), table_name='documents')
	op.drop_table('documents')
	op.drop_index(op.f('ix_users_email'), table_name='users')
	op.drop_table('users')

	document_status_enum.drop(op.get_bind(), checkfirst=True)
	source_type_enum.drop(op.get_bind(), checkfirst=True)
	owner_type_enum.drop(op.get_bind(), checkfirst=True)
