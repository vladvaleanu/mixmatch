"""Modelul de date. Sursa de adevăr pentru tabele; migrările Alembic îl urmează."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, Enum, MetaData, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(UTC)


# Nume stabile pentru constrângeri, ca migrările pe SQLite (batch) să le poată găsi.
NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


class Track(Base):
    __tablename__ = "tracks"
    __table_args__ = (
        CheckConstraint("energy BETWEEN 1 AND 5", name="energy_range"),
        CheckConstraint("energy_manual BETWEEN 1 AND 5", name="energy_manual_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(Text, unique=True)
    file_hash: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(Text)
    artist: Mapped[str | None] = mapped_column(Text)
    duration_s: Mapped[float]
    bpm: Mapped[float | None]
    key_camelot: Mapped[str | None] = mapped_column(String(3))
    energy: Mapped[int | None]
    energy_manual: Mapped[int | None]
    first_beat_s: Mapped[float | None]
    intro_bars: Mapped[int | None]
    outro_bars: Mapped[int | None]
    analysis_version: Mapped[int | None]
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LibraryFolder(Base):
    __tablename__ = "library_folders"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(Text, unique=True)
    last_scan_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class JobKind(StrEnum):
    scan = "scan"
    analysis = "analysis"
    export = "export"


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (CheckConstraint("progress BETWEEN 0 AND 1", name="progress_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[JobKind] = mapped_column(Enum(JobKind, native_enum=False, length=16))
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=16), default=JobStatus.queued
    )
    progress: Mapped[float] = mapped_column(default=0.0)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
