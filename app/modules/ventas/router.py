"""Rutas de ventas.

No se publican `POST /ventas/` ni `PATCH /ventas/{id}`: el alta pertenece al
change `04` y la tabla de referencia no define actualización. Como el path
existe con `GET`, esos métodos responden `405`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.ventas import service
from app.modules.ventas.schemas import VentaRead, VentaResumenRead

router = APIRouter(prefix="/ventas", tags=["ventas"])


@router.get("/", response_model=list[VentaResumenRead], summary="Listar ventas")
async def listar_ventas(
    session: Annotated[AsyncSession, Depends(get_session)],
    pagina: Annotated[Paginacion, Depends(paginacion)],
) -> list[VentaResumenRead]:
    """Lista ventas ordenadas por `id` con paginación."""
    return await service.listar_ventas(session, pagina)


@router.get("/{id}", response_model=VentaRead, summary="Obtener una venta")
async def obtener_venta(
    id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> VentaRead:
    """Devuelve el detalle con cliente y renglones con `subtotal`."""
    return await service.obtener_venta(session, id)
