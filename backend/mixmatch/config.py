"""Setările aplicației, citite o singură dată la pornire.

Folderul de date se poate schimba cu variabila de mediu MIXMATCH_DATA_DIR.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

APP_VERSION = "0.1.0"

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent


def _default_data_dir() -> Path:
    return Path(os.environ.get("MIXMATCH_DATA_DIR", REPO_DIR / "data"))


@dataclass(frozen=True)
class Settings:
    version: str = APP_VERSION
    data_dir: Path = field(default_factory=_default_data_dir)

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'mixmatch.db'}"


settings = Settings()
