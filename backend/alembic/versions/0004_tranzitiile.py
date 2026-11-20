"""tranzițiile

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transitions",
        sa.Column("mix_id", sa.Integer(), nullable=False),
        sa.Column("from_track_id", sa.Integer(), nullable=False),
        sa.Column("to_track_id", sa.Integer(), nullable=False),
        sa.Column("length_bars", sa.Integer(), nullable=False),
        sa.Column(
            "style",
            sa.Enum(
                "eq_swap",
                "crossfade",
                "echo_out",
                "cut",
                name="style",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("a_out_s", sa.Double(), nullable=True),
        sa.Column("b_in_s", sa.Double(), nullable=True),
        sa.ForeignKeyConstraint(
            ["from_track_id"],
            ["tracks.id"],
            name=op.f("fk_transitions_from_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["mix_id"], ["mixes.id"], name=op.f("fk_transitions_mix_id_mixes"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["to_track_id"],
            ["tracks.id"],
            name=op.f("fk_transitions_to_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "mix_id", "from_track_id", "to_track_id", name=op.f("pk_transitions")
        ),
    )


def downgrade() -> None:
    op.drop_table("transitions")
