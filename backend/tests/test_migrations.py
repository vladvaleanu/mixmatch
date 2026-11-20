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
