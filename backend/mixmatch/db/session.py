"""Conexiunea la SQLite, sesiunile și rularea migrărilor."""

from pathlib import Path

from alembic.config import Config
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import sessionmaker

from alembic import command
from mixmatch.config import BACKEND_DIR, settings


def create_db_engine(url: str) -> Engine:
    # check_same_thread=False: sesiunile se folosesc și din firele cozii de joburi.
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.close()

    return engine


def run_migrations(url: str) -> None:
    """Aduce baza de la `url` la ultima migrare. Creează fișierul dacă lipsește."""
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    config = Config(BACKEND_DIR / "alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")


engine = create_db_engine(settings.db_url)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
