from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from mixmatch.db.models import Base
from mixmatch.db.session import create_db_engine


def test_migration_creates_tables_on_empty_db(db_url: str) -> None:
    engine = create_db_engine(db_url)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()
    assert {"tracks", "library_folders", "jobs", "alembic_version"} <= tables


def test_models_match_migrations(db_url: str) -> None:
    engine = create_db_engine(db_url)
    with engine.connect() as conn:
        context = MigrationContext.configure(conn, opts={"compare_type": True})
        diff = compare_metadata(context, Base.metadata)
    engine.dispose()
    assert diff == [], (
        f"Modelele diferă de migrări; rulează alembic revision --autogenerate: {diff}"
    )


def test_upgrades_keep_rows_that_point_to_tracks(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """O migrare care recreează `tracks` (batch) nu are voie să șteargă în cascadă ce trimite
    spre ea. Regresie: 0008 a golit waveforms, beat_grids, mix_items și transitions."""
    from alembic.config import Config

    from alembic import command
    from mixmatch.config import BACKEND_DIR

    url = f"sqlite:///{tmp_path / 'old.db'}"
    config = Config(BACKEND_DIR / "alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "0007")

    engine = create_db_engine(url)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "INSERT INTO tracks (id, path, file_hash, title, duration_s)"
            " VALUES (1, '/a', 'h', 'A', 300), (2, '/b', 'g', 'B', 300)"
        )
        conn.exec_driver_sql("INSERT INTO waveforms VALUES (1, x'00', x'00', x'00')")
        conn.exec_driver_sql("INSERT INTO beat_grids VALUES (1, x'00000000')")
        conn.exec_driver_sql(
            "INSERT INTO mixes (id, name, energy_shape, created_at, updated_at)"
            " VALUES (1, 'M', 'free', '2026-01-01', '2026-01-01')"
        )
        conn.exec_driver_sql("INSERT INTO mix_items VALUES (1, 0, 1), (1, 1, 2)")
        conn.exec_driver_sql(
            "INSERT INTO transitions VALUES (1, 1, 2, 16, 'eq_swap', NULL, NULL, 0.02)"
        )
    engine.dispose()

    command.upgrade(config, "head")

    engine = create_db_engine(url)
    with engine.connect() as conn:
        counts = {
            table: conn.exec_driver_sql(f"SELECT COUNT(*) FROM {table}").scalar()
            for table in ("tracks", "waveforms", "beat_grids", "mix_items", "transitions")
        }
    engine.dispose()
    assert counts == {
        "tracks": 2,
        "waveforms": 1,
        "beat_grids": 1,
        "mix_items": 2,
        "transitions": 1,
    }
