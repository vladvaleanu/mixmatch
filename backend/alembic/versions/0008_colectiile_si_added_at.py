"""colecțiile și tracks.added_at

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "collections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collections")),
        sa.UniqueConstraint("name", name=op.f("uq_collections_name")),
    )
    op.create_table(
        "collection_tracks",
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["collections.id"],
            name=op.f("fk_collection_tracks_collection_id_collections"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_collection_tracks_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("collection_id", "track_id", name=op.f("pk_collection_tracks")),
    )
    with op.batch_alter_table("collection_tracks", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_collection_tracks_track_id"), ["track_id"], unique=False
        )

    with op.batch_alter_table("tracks", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "added_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("tracks", schema=None) as batch_op:
        batch_op.drop_column("added_at")

    with op.batch_alter_table("collection_tracks", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_collection_tracks_track_id"))

    op.drop_table("collection_tracks")
    op.drop_table("collections")
