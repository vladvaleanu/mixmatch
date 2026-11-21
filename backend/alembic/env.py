"""Rulează migrările pe baza din `sqlalchemy.url` sau, dacă lipsește, pe cea din config.

Migrările rulează cu cheile externe dezactivate: în SQLite, o modificare de tabel în mod batch
recreează tabela (copiere, apoi ștergerea celei vechi), iar cu cheile externe active ștergerea
ar declanșa ON DELETE CASCADE pe tot ce trimite spre ea. Asta s-a întâmplat la 0008 (formele de
undă, grilele de beat-uri și piesele din mixuri au fost șterse). După migrări, integritatea se
verifică explicit cu PRAGMA foreign_key_check.
"""

from sqlalchemy import create_engine

from alembic import context
from mixmatch.config import settings
from mixmatch.db.models import Base

config = context.config
url = config.get_main_option("sqlalchemy.url") or settings.db_url

# Un engine simplu, fără PRAGMA foreign_keys = ON (implicit în SQLite e OFF).
engine = create_engine(url)
with engine.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()
    broken = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
    if broken:
        raise RuntimeError(f"Migrările au lăsat referințe rupte: {broken[:5]}")
engine.dispose()
