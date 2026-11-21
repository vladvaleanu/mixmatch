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


def _default_uploads_dir() -> Path:
    return Path(
        os.environ.get("MIXMATCH_UPLOAD_DIR", Path.home() / "Music" / "mixmatch" / "Importate")
    )


def _default_exports_dir() -> Path:
    return Path(os.environ.get("MIXMATCH_EXPORT_DIR", Path.home() / "Music" / "mixmatch"))


def _default_frontend_dir() -> Path:
    return Path(os.environ.get("MIXMATCH_FRONTEND_DIR", REPO_DIR / "frontend" / "dist"))


@dataclass(frozen=True)
class Settings:
    version: str = APP_VERSION
    data_dir: Path = field(default_factory=_default_data_dir)
    # Unde se scriu exporturile: câte un folder pe mix (audio, tracklist, .cue).
    exports_dir: Path = field(default_factory=_default_exports_dir)
    # Folderul administrat în care se copiază fișierele trase în Bibliotecă (drag & drop).
    uploads_dir: Path = field(default_factory=_default_uploads_dir)
    # Interfața compilată (`npm run build`); servită de backend doar dacă există (pe server).
    frontend_dir: Path = field(default_factory=_default_frontend_dir)
    # Formatele pe care le scanează biblioteca.
    audio_extensions: frozenset[str] = frozenset({".mp3", ".flac", ".wav", ".aif", ".aiff", ".m4a"})
    # Fișierele mai scurte (sample-uri, jingle-uri) nu intră în bibliotecă.
    min_duration_s: float = 60.0
    # Crește când se schimbă algoritmii de analiză: piesele analizate cu o versiune mai veche
    # se reanalizează automat.
    # 2: energie, tărie, formă de undă, intro/outro; 3: undă RMS; 4: decodare cu ffmpeg;
    # 5: toate beat-urile, cu faza corectată pe kick
    analysis_version: int = 5
    # Câte piese se analizează în paralel (procese separate).
    analysis_workers: int = field(default_factory=lambda: max(1, min(6, (os.cpu_count() or 2) - 2)))

    @property
    def cache_dir(self) -> Path:
        """Fișiere derivate, refăcute oricând (ex. AIFF convertite pentru browser)."""
        return self.data_dir / "cache"

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'mixmatch.db'}"


settings = Settings()
