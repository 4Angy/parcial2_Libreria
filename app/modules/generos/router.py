"""Rutas de géneros."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.generos import service
from app.modules.generos.schemas import GeneroCreate, GeneroRead
from app.modules.libros.schemas import LibroResumenRead

router = APIRouter(prefix="/generos", tags=["generos"])


@router.post(
    "/",
    response_model=GeneroRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un género",
)
async def crear_genero(
    datos: GeneroCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GeneroRead:
    """Crea un género; un nombre repetido responde `409`."""
    return await service.crear_genero(session, datos)


@router.get("/", response_model=list[GeneroRead], summary="Listar géneros")
async def listar_generos(
    session: Annotated[AsyncSession, Depends(get_session)],
    pagina: Annotated[Paginacion, Depends(paginacion)],
) -> list[GeneroRead]:
    """Lista géneros ordenados por `id` con paginación."""
    return await service.listar_generos(session, pagina)


@router.get(
    "/{id}/libros",
    response_model=list[LibroResumenRead],
    summary="Listar los libros de un género",
)
async def listar_libros_de_genero(
    id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    pagina: Annotated[Paginacion, Depends(paginacion)],
) -> list[LibroResumenRead]:
    """Devuelve los libros del género o `404` si no existe."""
    return await service.listar_libros_de_genero(session, id, pagina)
