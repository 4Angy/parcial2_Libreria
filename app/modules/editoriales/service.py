"""Reglas de negocio de editoriales.

El servicio no conoce códigos HTTP: lanza `NoEncontrado`/`Conflicto` y deja
que el router y el handler compartido construyan la respuesta.
"""

from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import NoEncontrado, confirmar
from app.core.pagination import Paginacion
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate, EditorialUpdate
from app.modules.libros.models import Libro

_MENSAJE_NO_ENCONTRADA = "La editorial no existe."
_MENSAJE_CONFLICTO = "Ya existe una editorial con ese nombre."


async def listar_editoriales(
    session: AsyncSession, paginacion: Paginacion
) -> list[Editorial]:
    """Devuelve una página de editoriales ordenada por `id`."""
    consulta = (
        select(Editorial)
        .order_by(Editorial.id)
        .offset(paginacion.offset)
        .limit(paginacion.limit)
    )
    return list((await session.execute(consulta)).scalars().all())


async def crear_editorial(
    session: AsyncSession, datos: EditorialCreate
) -> Editorial:
    """Inserta una editorial y traduce el nombre repetido a `409`."""
    editorial = Editorial(**datos.model_dump())
    session.add(editorial)
    await confirmar(session, _MENSAJE_CONFLICTO)
    return editorial


async def obtener_editorial(session: AsyncSession, editorial_id: int) -> Editorial:
    """Busca una editorial por `id` o lanza `NoEncontrado`."""
    editorial = await session.get(Editorial, editorial_id)
    if editorial is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADA)
    return editorial


async def actualizar_editorial(
    session: AsyncSession, editorial_id: int, datos: EditorialUpdate
) -> Editorial:
    """Aplica solo los campos enviados; un cuerpo vacío no escribe nada."""
    editorial = await obtener_editorial(session, editorial_id)
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        return editorial

    editorial.sqlmodel_update(cambios)
    session.add(editorial)
    await confirmar(session, _MENSAJE_CONFLICTO)
    return editorial


async def listar_libros_de_editorial(
    session: AsyncSession, editorial_id: int, paginacion: Paginacion
) -> list[Libro]:
    """Devuelve una página de libros de la editorial con sus referencias."""
    editorial = await session.get(Editorial, editorial_id)
    if editorial is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADA)

    consulta = (
        select(Libro)
        .where(Libro.editorial_id == editorial_id)
        .options(joinedload(Libro.editorial), joinedload(Libro.genero))
        .order_by(Libro.id)
        .offset(paginacion.offset)
        .limit(paginacion.limit)
    )
    return list((await session.execute(consulta)).scalars().all())
