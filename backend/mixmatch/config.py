"""Setările aplicației, citite o singură dată la pornire."""

from dataclasses import dataclass

APP_VERSION = "0.1.0"


@dataclass(frozen=True)
class Settings:
    version: str = APP_VERSION


settings = Settings()
