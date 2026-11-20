"""grilele de beat-uri

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "beat_grids",
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("beats", sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_beat_grids_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("track_id", name=op.f("pk_beat_grids")),
    )


def downgrade() -> None:
    op.drop_table("beat_grids")
