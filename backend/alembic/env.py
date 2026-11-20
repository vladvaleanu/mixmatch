"""Rulează migrările pe baza din `sqlalchemy.url` sau, dacă lipsește, pe cea din config."""

from alembic import context
from mixmatch.config import settings
from mixmatch.db.models import Base
from mixmatch.db.session import create_db_engine

config = context.config
url = config.get_main_option("sqlalchemy.url") or settings.db_url

engine = create_db_engine(url)
with engine.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()
engine.dispose()
