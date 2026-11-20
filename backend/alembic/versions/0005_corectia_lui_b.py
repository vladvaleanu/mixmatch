"""transitions.b_nudge_s: corecția manuală a lui B

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("transitions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("b_nudge_s", sa.Double(), server_default="0", nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("transitions", schema=None) as batch_op:
        batch_op.drop_column("b_nudge_s")
