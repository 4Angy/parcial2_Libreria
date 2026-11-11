"""Reglas de negocio de autores.

La navegación hacia los libros pasa por `LibroAutor`, que conserva el rol y
el orden de cada participación. El sublistado carga el libro y sus referencias
con `joinedload` para no depender de la carga perezosa.
"""

from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import NoEncontrado, confirmar
from app.core.pagination import Paginacion
from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorUpdate
from app.modules.libros.models import Libro, LibroAutor

_MENSAJE_NO_ENCONTRADO = "El autor no existe."
_MENSAJE_CONFLICTO = "Ya existe un autor con ese nombre."


async def crear_autor(session: AsyncSession, datos: AutorCreate) -> Autor:
    """Inserta un autor y confirma la transacción."""
    autor = Autor(**datos.model_dump())
    session.add(autor)
    await confirmar(session, _MENSAJE_CONFLICTO)
    return autor


async def obtener_autor(session: AsyncSession, autor_id: int) -> Autor:
    """Busca un autor por `id` o lanza `NoEncontrado`."""
    autor = await session.get(Autor, autor_id)
    if autor is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADO)
    return autor


async def actualizar_autor(
    session: AsyncSession, autor_id: int, datos: AutorUpdate
) -> Autor:
    """Aplica solo los campos enviados; un cuerpo vacío no escribe nada."""
    autor = await obtener_autor(session, autor_id)
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        return autor

    autor.sqlmodel_update(cambios)
    session.add(autor)
    await confirmar(session, _MENSAJE_CONFLICTO)
    return autor


async def listar_autorias_de_autor(
    session: AsyncSession, autor_id: int, paginacion: Paginacion
) -> list[LibroAutor]:
    """Devuelve una página de participaciones del autor con su libro."""
    autor = await session.get(Autor, autor_id)
    if autor is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADO)

    consulta = (
        select(LibroAutor)
        .where(LibroAutor.autor_id == autor_id)
        .options(
            joinedload(LibroAutor.libro).joinedload(Libro.editorial),
            joinedload(LibroAutor.libro).joinedload(Libro.genero),
        )
        .order_by(LibroAutor.orden, LibroAutor.libro_id)
        .offset(paginacion.offset)
        .limit(paginacion.limit)
    )
    return list((await session.execute(consulta)).scalars().all())
