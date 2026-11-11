"""Rutas de autores."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.autores import service
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate
from app.modules.libros.schemas import LibroDeAutorRead

router = APIRouter(prefix="/autores", tags=["autores"])


@router.post(
    "/",
    response_model=AutorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un autor",
)
async def crear_autor(
    datos: AutorCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AutorRead:
    """Crea un autor y devuelve su `id`."""
    return await service.crear_autor(session, datos)


@router.get("/{id}", response_model=AutorRead, summary="Obtener un autor")
async def obtener_autor(
    id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AutorRead:
    """Devuelve un autor o `404` si no existe."""
    return await service.obtener_autor(session, id)


@router.patch(
    "/{id}", response_model=AutorRead, summary="Actualizar un autor"
)
async def actualizar_autor(
    id: int,
    datos: AutorUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AutorRead:
    """Aplica un `PATCH` parcial y devuelve el estado actualizado."""
    return await service.actualizar_autor(session, id, datos)


@router.get(
    "/{id}/libros",
    response_model=list[LibroDeAutorRead],
    summary="Listar los libros de un autor",
)
async def listar_libros_de_autor(
    id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    pagina: Annotated[Paginacion, Depends(paginacion)],
) -> list[LibroDeAutorRead]:
    """Devuelve cada participación con su libro, `rol` y `orden`."""
    return await service.listar_autorias_de_autor(session, id, pagina)
