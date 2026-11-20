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
    # Formatele pe care le scanează biblioteca.
    audio_extensions: frozenset[str] = frozenset({".mp3", ".flac", ".wav", ".aif", ".aiff", ".m4a"})
    # Fișierele mai scurte (sample-uri, jingle-uri) nu intră în bibliotecă.
    min_duration_s: float = 60.0
    # Crește când se schimbă algoritmii de analiză: piesele analizate cu o versiune mai veche
    # se reanalizează automat.
    analysis_version: int = 1
    # Câte piese se analizează în paralel (procese separate).
    analysis_workers: int = field(default_factory=lambda: max(1, min(6, (os.cpu_count() or 2) - 2)))

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'mixmatch.db'}"


settings = Settings()
