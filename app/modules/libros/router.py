"""Rutas de libros.

El alta recibe `LibroCreate` con los ids de la editorial, del género y de los
autores que ya existen. El resto de las rutas mantiene el contrato del `03`.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.libros import service
from app.modules.libros.schemas import (
    LibroCreate,
    LibroRead,
    LibroResumenRead,
    LibroUpdate,
)

router = APIRouter(prefix="/libros", tags=["libros"])


@router.post(
    "/", response_model=LibroRead, status_code=201, summary="Crear un libro"
)
async def crear_libro(
    datos: LibroCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LibroRead:
    """Registra el libro con sus autorías y devuelve el detalle."""
    return await service.crear_libro(session, datos)


@router.get("/", response_model=list[LibroResumenRead], summary="Listar libros")
async def listar_libros(
    session: Annotated[AsyncSession, Depends(get_session)],
    pagina: Annotated[Paginacion, Depends(paginacion)],
    titulo: Annotated[Optional[str], Query()] = None,
    genero_id: Annotated[Optional[int], Query()] = None,
) -> list[LibroResumenRead]:
    """Lista libros con búsqueda parcial por título y filtro por género."""
    return await service.listar_libros(session, pagina, titulo, genero_id)


@router.get("/{id}", response_model=LibroRead, summary="Obtener un libro")
async def obtener_libro(
    id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LibroRead:
    """Devuelve el detalle con editorial, género y autores."""
    return await service.obtener_libro(session, id)


@router.patch(
    "/{id}", response_model=LibroRead, summary="Actualizar un libro"
)
async def actualizar_libro(
    id: int,
    datos: LibroUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LibroRead:
    """Aplica un `PATCH` parcial y devuelve el detalle actualizado."""
    return await service.actualizar_libro(session, id, datos)
