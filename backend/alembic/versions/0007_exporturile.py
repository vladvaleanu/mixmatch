"""exporturile

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "exports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mix_id", sa.Integer(), nullable=True),
        sa.Column("mix_name", sa.Text(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("format", sa.String(length=8), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("duration_s", sa.Double(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name=op.f("fk_exports_job_id_jobs"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["mix_id"], ["mixes.id"], name=op.f("fk_exports_mix_id_mixes"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exports")),
    )


def downgrade() -> None:
    op.drop_table("exports")
