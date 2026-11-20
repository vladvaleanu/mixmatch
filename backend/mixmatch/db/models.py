"""Modelul de date. Sursa de adevăr pentru tabele; migrările Alembic îl urmează."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    LargeBinary,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from mixmatch.music.energy_curve import EnergyShape
from mixmatch.music.transition_plan import Style


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
    loudness_lufs: Mapped[float | None]
    first_beat_s: Mapped[float | None]
    intro_bars: Mapped[int | None]
    outro_bars: Mapped[int | None]
    analysis_version: Mapped[int | None]
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    waveform: Mapped["Waveform | None"] = relationship(
        back_populates="track", cascade="all, delete-orphan", passive_deletes=True, lazy="raise"
    )

    @hybrid_property
    def energy_effective(self) -> int | None:
        """Singurul loc unde se alege energia afișată: corectura manuală are prioritate."""
        return self.energy_manual if self.energy_manual is not None else self.energy

    @energy_effective.inplace.expression
    @classmethod
    def _energy_effective_sql(cls):  # type: ignore[no-untyped-def]
        return func.coalesce(cls.energy_manual, cls.energy)


class BeatGridRow(Base):
    """Toate beat-urile unei piese (float32, secunde), cu faza corectată pe kick."""

    __tablename__ = "beat_grids"

    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True
    )
    beats: Mapped[bytes] = mapped_column(LargeBinary)


class Waveform(Base):
    """Vârfurile formei de undă (octeți 0–255): previzualizare (40), listă (1000), editor (8000)."""

    __tablename__ = "waveforms"

    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True
    )
    preview: Mapped[bytes] = mapped_column(LargeBinary)
    peaks: Mapped[bytes] = mapped_column(LargeBinary)
    peaks_hi: Mapped[bytes] = mapped_column(LargeBinary)

    track: Mapped[Track] = relationship(back_populates="waveform")


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


class Mix(Base):
    __tablename__ = "mixes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    energy_shape: Mapped[EnergyShape] = mapped_column(
        Enum(EnergyShape, native_enum=False, length=16), default=EnergyShape.free
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    items: Mapped[list["MixItem"]] = relationship(
        back_populates="mix",
        order_by="MixItem.position",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class MixItem(Base):
    """O piesă pe o poziție în mix. O piesă apare cel mult o dată într-un mix."""

    __tablename__ = "mix_items"
    __table_args__ = (UniqueConstraint("mix_id", "track_id", name="track_once"),)

    mix_id: Mapped[int] = mapped_column(
        ForeignKey("mixes.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(primary_key=True)
    # O piesă ștearsă din bibliotecă (rescanare) dispare și din mixuri.
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), index=True)

    mix: Mapped[Mix] = relationship(back_populates="items")
    track: Mapped[Track] = relationship()


class Transition(Base):
    """Setările unei tranziții A → B dintr-un mix, legate de pereche (nu de poziție).

    Dacă A și B ajung din nou una după alta după o reordonare, setările revin. Rând lipsă =
    valorile implicite. `a_out_s` / `b_in_s` null = puncte alese automat.
    """

    __tablename__ = "transitions"

    mix_id: Mapped[int] = mapped_column(
        ForeignKey("mixes.id", ondelete="CASCADE"), primary_key=True
    )
    from_track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True
    )
    to_track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True
    )
    length_bars: Mapped[int]
    style: Mapped[Style] = mapped_column(Enum(Style, native_enum=False, length=16))
    a_out_s: Mapped[float | None]
    b_in_s: Mapped[float | None]
    # Corecția manuală a lui B (secunde, în timpul mixului): pozitiv = mai târziu.
    b_nudge_s: Mapped[float] = mapped_column(default=0.0, server_default="0")


class Export(Base):
    """Un mix exportat: fișierul audio, plus tracklistul și .cue cu același nume, alături."""

    __tablename__ = "exports"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Exportul rămâne în istoric și dacă mixul e șters.
    mix_id: Mapped[int | None] = mapped_column(ForeignKey("mixes.id", ondelete="SET NULL"))
    mix_name: Mapped[str] = mapped_column(Text)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"))
    format: Mapped[str] = mapped_column(String(8))
    path: Mapped[str] = mapped_column(Text)
    duration_s: Mapped[float | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
