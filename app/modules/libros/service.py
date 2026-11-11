"""Reglas de negocio de libros.

La búsqueda por título usa `ilike` y envía el patrón como parámetro ligado.
Las lecturas cargan editorial, género y autorías de forma anticipada: ninguna
serialización depende de la carga perezosa.
"""

from typing import Optional

from sqlalchemy import Select
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import NoEncontrado, confirmar
from app.core.pagination import Paginacion
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import LibroUpdate

_MENSAJE_NO_ENCONTRADO = "El libro no existe."
_MENSAJE_CONFLICTO = "El ISBN ya pertenece a otro libro."


def _consulta_libro() -> Select:
    """Arma la consulta base del detalle con todas sus relaciones cargadas."""
    return select(Libro).options(
        joinedload(Libro.editorial),
        joinedload(Libro.genero),
        selectinload(Libro.autorias).joinedload(LibroAutor.autor),
    )


async def listar_libros(
    session: AsyncSession,
    paginacion: Paginacion,
    titulo: Optional[str],
    genero_id: Optional[int],
) -> list[Libro]:
    """Lista libros con búsqueda parcial por título y filtro por género."""
    consulta = select(Libro).options(
        joinedload(Libro.editorial), joinedload(Libro.genero)
    )
    if titulo:
        consulta = consulta.where(Libro.titulo.ilike(f"%{titulo}%"))
    if genero_id is not None:
        consulta = consulta.where(Libro.genero_id == genero_id)

    consulta = (
        consulta.order_by(Libro.id)
        .offset(paginacion.offset)
        .limit(paginacion.limit)
    )
    return list((await session.execute(consulta)).scalars().all())


async def obtener_libro(session: AsyncSession, libro_id: int) -> Libro:
    """Busca un libro por `id` con sus relaciones o lanza `NoEncontrado`."""
    consulta = _consulta_libro().where(Libro.id == libro_id)
    libro = (await session.execute(consulta)).scalars().first()
    if libro is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADO)
    return libro


async def _releer_libro(session: AsyncSession, libro_id: int) -> Libro:
    """Vuelve a leer el libro forzando el refresco de sus relaciones.

    Con `expire_on_commit=False` la entidad conserva el estado previo al
    `commit`; `populate_existing` reemplaza los valores cargados para que el
    `PATCH` devuelva la editorial, el género y las autorías actuales.
    """
    consulta = _consulta_libro().where(Libro.id == libro_id)
    consulta = consulta.execution_options(populate_existing=True)
    libro = (await session.execute(consulta)).scalars().first()
    if libro is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADO)
    return libro


async def actualizar_libro(
    session: AsyncSession, libro_id: int, datos: LibroUpdate
) -> Libro:
    """Aplica solo los campos enviados y devuelve el detalle actualizado."""
    libro = await obtener_libro(session, libro_id)
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        return libro

    libro.sqlmodel_update(cambios)
    session.add(libro)
    await confirmar(session, _MENSAJE_CONFLICTO)
    return await _releer_libro(session, libro_id)
