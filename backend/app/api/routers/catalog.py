from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api import deps
from app.api.schemas import CatalogOut
from app.application.sessions import GetCatalog

router = APIRouter(tags=["catálogo"])


@router.get("/catalog", response_model=CatalogOut)
def catalog(use_case: Annotated[GetCatalog, Depends(deps.get_catalog)]):
    """Áreas, temas y tags, con cuántas preguntas activas tiene cada uno."""
    return use_case.execute()
