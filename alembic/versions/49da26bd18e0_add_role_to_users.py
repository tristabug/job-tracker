"""add role to users

Revision ID: 49da26bd18e0
Revises: daaf5b2453df
Create Date: 2026-06-13 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49da26bd18e0'
down_revision: Union[str, Sequence[str], None] = 'daaf5b2453df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column(
            'role',
            sa.Enum('DEMO', 'USER', 'ADMIN', name='userrole', native_enum=False),
            nullable=False,
            server_default='USER',
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')
