"""Exporta el contrato: python -m app.api.openapi > openapi.json"""
from __future__ import annotations

import json
import sys

from app.api.main import app


def schema_text() -> str:
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"


if __name__ == "__main__":
    sys.stdout.write(schema_text())
