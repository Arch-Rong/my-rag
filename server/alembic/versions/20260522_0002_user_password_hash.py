"""add users.password_hash for JWT login

Revision ID: 20260522_0002
Revises: 20260516_0001
Create Date: 2026-05-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '20260522_0002'
down_revision: Union[str, Sequence[str], None] = '20260516_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.add_column(
		'users',
		sa.Column('password_hash', sa.String(length=255), nullable=True),
	)


def downgrade() -> None:
	op.drop_column('users', 'password_hash')
