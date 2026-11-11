"""Rutas de clientes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.clientes import service
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
    PerfilCreate,
    PerfilRead,
)
from app.modules.ventas.schemas import VentaResumenRead

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post(
    "/",
    response_model=ClienteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un cliente",
)
async def crear_cliente(
    datos: ClienteCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ClienteRead:
    """Crea un cliente; un email repetido responde `409`."""
    return await service.crear_cliente(session, datos)


@router.get(
    "/{id}", response_model=ClienteRead, summary="Obtener un cliente"
)
async def obtener_cliente(
    id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ClienteRead:
    """Devuelve un cliente con su perfil como objeto o `null`."""
    return await service.obtener_cliente(session, id)


@router.patch(
    "/{id}", response_model=ClienteRead, summary="Actualizar un cliente"
)
async def actualizar_cliente(
    id: int,
    datos: ClienteUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ClienteRead:
    """Aplica un `PATCH` parcial y conserva el perfil del cliente."""
    return await service.actualizar_cliente(session, id, datos)


@router.post(
    "/{id}/perfil",
    response_model=PerfilRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear el perfil de un cliente",
)
async def crear_perfil(
    id: int,
    datos: PerfilCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PerfilRead:
    """Crea el perfil de un cliente existente; el segundo responde `409`."""
    return await service.crear_perfil(session, id, datos)


@router.get(
    "/{id}/ventas",
    response_model=list[VentaResumenRead],
    summary="Listar las ventas de un cliente",
)
async def listar_ventas_de_cliente(
    id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    pagina: Annotated[Paginacion, Depends(paginacion)],
) -> list[VentaResumenRead]:
    """Devuelve las ventas del cliente o `404` si no existe."""
    return await service.listar_ventas_de_cliente(session, id, pagina)
