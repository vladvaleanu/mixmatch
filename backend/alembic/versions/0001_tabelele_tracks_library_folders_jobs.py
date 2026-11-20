"""tabelele tracks, library_folders, jobs

Revision ID: 0001
Revises:
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("scan", "analysis", "export", name="jobkind", native_enum=False, length=16),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "running",
                "done",
                "failed",
                name="jobstatus",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("progress", sa.Double(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("progress BETWEEN 0 AND 1", name=op.f("ck_jobs_progress_range")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
    )
    op.create_table(
        "library_folders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("last_scan_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_library_folders")),
        sa.UniqueConstraint("path", name=op.f("uq_library_folders_path")),
    )
    op.create_table(
        "tracks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("artist", sa.Text(), nullable=True),
        sa.Column("duration_s", sa.Double(), nullable=False),
        sa.Column("bpm", sa.Double(), nullable=True),
        sa.Column("key_camelot", sa.String(length=3), nullable=True),
        sa.Column("energy", sa.Integer(), nullable=True),
        sa.Column("energy_manual", sa.Integer(), nullable=True),
        sa.Column("first_beat_s", sa.Double(), nullable=True),
        sa.Column("intro_bars", sa.Integer(), nullable=True),
        sa.Column("outro_bars", sa.Integer(), nullable=True),
        sa.Column("analysis_version", sa.Integer(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("energy BETWEEN 1 AND 5", name=op.f("ck_tracks_energy_range")),
        sa.CheckConstraint(
            "energy_manual BETWEEN 1 AND 5", name=op.f("ck_tracks_energy_manual_range")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tracks")),
        sa.UniqueConstraint("path", name=op.f("uq_tracks_path")),
    )
    with op.batch_alter_table("tracks", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_tracks_file_hash"), ["file_hash"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("tracks", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_tracks_file_hash"))

    op.drop_table("tracks")
    op.drop_table("library_folders")
    op.drop_table("jobs")
