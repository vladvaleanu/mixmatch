import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# Înainte de orice import din mixmatch: aplicația nu are voie să atingă data/ din repo.
os.environ.setdefault("MIXMATCH_DATA_DIR", tempfile.mkdtemp(prefix="mixmatch-test-"))

from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from mixmatch.db.session import create_db_engine, run_migrations  # noqa: E402


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    url = f"sqlite:///{tmp_path / 'test.db'}"
    run_migrations(url)
    return url


@pytest.fixture
def sessions(db_url: str) -> Iterator[sessionmaker[Session]]:
    engine = create_db_engine(db_url)
    yield sessionmaker(engine, expire_on_commit=False)
    engine.dispose()
