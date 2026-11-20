"""mixurile

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mixes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "energy_shape",
            sa.Enum(
                "warmup", "rise", "wave", "free", name="energyshape", native_enum=False, length=16
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mixes")),
    )
    op.create_table(
        "mix_items",
        sa.Column("mix_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["mix_id"], ["mixes.id"], name=op.f("fk_mix_items_mix_id_mixes"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_mix_items_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("mix_id", "position", name=op.f("pk_mix_items")),
        sa.UniqueConstraint("mix_id", "track_id", name="track_once"),
    )
    with op.batch_alter_table("mix_items", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_mix_items_track_id"), ["track_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("mix_items", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_mix_items_track_id"))

    op.drop_table("mix_items")
    op.drop_table("mixes")
