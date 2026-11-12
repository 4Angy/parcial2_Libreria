"""Rutas de ventas.

El alta recibe `VentaCreate` con el cliente y los renglones. `PATCH
/ventas/{id}` sigue sin declararse: como el path existe con `GET`, responde
`405` (RN-08).
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.ventas import service
from app.modules.ventas.schemas import VentaCreate, VentaRead, VentaResumenRead

router = APIRouter(prefix="/ventas", tags=["ventas"])


@router.post(
    "/", response_model=VentaRead, status_code=201, summary="Registrar una venta"
)
async def crear_venta(
    datos: VentaCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> VentaRead:
    """Registra la venta con sus renglones y devuelve el detalle."""
    return await service.crear_venta(session, datos)


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
