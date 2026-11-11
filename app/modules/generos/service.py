"""Reglas de negocio de géneros."""

from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import NoEncontrado, confirmar
from app.core.pagination import Paginacion
from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate
from app.modules.libros.models import Libro

_MENSAJE_NO_ENCONTRADO = "El género no existe."
_MENSAJE_CONFLICTO = "Ya existe un género con ese nombre."


async def listar_generos(
    session: AsyncSession, paginacion: Paginacion
) -> list[Genero]:
    """Devuelve una página de géneros ordenada por `id`."""
    consulta = (
        select(Genero)
        .order_by(Genero.id)
        .offset(paginacion.offset)
        .limit(paginacion.limit)
    )
    return list((await session.execute(consulta)).scalars().all())


async def crear_genero(session: AsyncSession, datos: GeneroCreate) -> Genero:
    """Inserta un género y traduce el nombre repetido a `409`."""
    genero = Genero(**datos.model_dump())
    session.add(genero)
    await confirmar(session, _MENSAJE_CONFLICTO)
    return genero


async def listar_libros_de_genero(
    session: AsyncSession, genero_id: int, paginacion: Paginacion
) -> list[Libro]:
    """Devuelve una página de libros del género con sus referencias."""
    genero = await session.get(Genero, genero_id)
    if genero is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADO)

    consulta = (
        select(Libro)
        .where(Libro.genero_id == genero_id)
        .options(joinedload(Libro.editorial), joinedload(Libro.genero))
        .order_by(Libro.id)
        .offset(paginacion.offset)
        .limit(paginacion.limit)
    )
    return list((await session.execute(consulta)).scalars().all())
