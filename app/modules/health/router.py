"""Rutas de salud del proceso y de su dependencia con la base."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session

router = APIRouter(tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    """Informa que el proceso está vivo, sin consultar la base."""
    return {"estado": "vivo"}


@router.get("/ready")
async def ready(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JSONResponse:
    """Comprueba con `SELECT 1` que la base responde.

    Ante un fallo de la base responde `503` con un cuerpo genérico: el texto
    interno del error no se expone al cliente.
    """
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"estado": "no_listo", "base": "no_disponible"},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"estado": "listo", "base": "disponible"},
    )
