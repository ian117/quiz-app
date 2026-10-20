"""El contrato (OpenAPI) que consume el frontend no cambia sin que alguien lo note."""
from __future__ import annotations

from pathlib import Path

from app.api.openapi import schema_text

SNAPSHOT = Path(__file__).resolve().parents[2] / "openapi.json"


def test_openapi_json_esta_al_dia():
    assert SNAPSHOT.read_text(encoding="utf-8") == schema_text(), (
        "El contrato cambió. Si es intencionado: "
        "cd backend && PYTHONPATH=.:.. .venv/bin/python -m app.api.openapi > openapi.json"
    )
