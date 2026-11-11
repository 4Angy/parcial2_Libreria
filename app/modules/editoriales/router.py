"""Rutas de editoriales."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.editoriales import service
from app.modules.editoriales.schemas import (
    EditorialCreate,
    EditorialRead,
    EditorialUpdate,
)
from app.modules.libros.schemas import LibroResumenRead

router = APIRouter(prefix="/editoriales", tags=["editoriales"])


@router.post(
    "/",
    response_model=EditorialRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una editorial",
)
async def crear_editorial(
    datos: EditorialCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EditorialRead:
    """Crea una editorial; un nombre repetido responde `409`."""
    return await service.crear_editorial(session, datos)


@router.get("/", response_model=list[EditorialRead], summary="Listar editoriales")
async def listar_editoriales(
    session: Annotated[AsyncSession, Depends(get_session)],
    pagina: Annotated[Paginacion, Depends(paginacion)],
) -> list[EditorialRead]:
    """Lista editoriales ordenadas por `id` con paginación."""
    return await service.listar_editoriales(session, pagina)


@router.get(
    "/{id}",
    response_model=EditorialRead,
    summary="Obtener una editorial",
)
async def obtener_editorial(
    id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EditorialRead:
    """Devuelve una editorial o `404` si no existe."""
    return await service.obtener_editorial(session, id)


@router.patch(
    "/{id}",
    response_model=EditorialRead,
    summary="Actualizar una editorial",
)
async def actualizar_editorial(
    id: int,
    datos: EditorialUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EditorialRead:
    """Aplica un `PATCH` parcial y devuelve el estado actualizado."""
    return await service.actualizar_editorial(session, id, datos)


@router.get(
    "/{id}/libros",
    response_model=list[LibroResumenRead],
    summary="Listar los libros de una editorial",
)
async def listar_libros_de_editorial(
    id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    pagina: Annotated[Paginacion, Depends(paginacion)],
) -> list[LibroResumenRead]:
    """Devuelve los libros de la editorial o `404` si no existe."""
    return await service.listar_libros_de_editorial(session, id, pagina)
