"""tracks.loudness_lufs și tabelul waveforms

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "waveforms",
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("preview", sa.LargeBinary(), nullable=False),
        sa.Column("peaks", sa.LargeBinary(), nullable=False),
        sa.Column("peaks_hi", sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_waveforms_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("track_id", name=op.f("pk_waveforms")),
    )
    with op.batch_alter_table("tracks", schema=None) as batch_op:
        batch_op.add_column(sa.Column("loudness_lufs", sa.Double(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tracks", schema=None) as batch_op:
        batch_op.drop_column("loudness_lufs")

    op.drop_table("waveforms")
