"""Configuración de la API desde variables de entorno."""
from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def cors_origins_from_env() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return [o.strip() for o in raw.split(",") if o.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str

    @classmethod
    def from_env(cls) -> Settings:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("Falta la variable DATABASE_URL")
        return cls(database_url)
