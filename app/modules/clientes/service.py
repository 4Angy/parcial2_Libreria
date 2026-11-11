"""Reglas de negocio de clientes y de sus perfiles.

El alta de un cliente devuelve `ClienteRead` con `perfil=None` porque un
cliente recién creado no puede tener perfil y no se permite una carga
perezosa. El perfil único por cliente lo garantiza la base: el segundo alta
se traduce a `409`.
"""

from sqlalchemy import Select
from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import NoEncontrado, confirmar
from app.core.pagination import Paginacion
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
    PerfilCreate,
)
from app.modules.ventas.models import Venta

_MENSAJE_NO_ENCONTRADO = "El cliente no existe."
_MENSAJE_CONFLICTO_EMAIL = "Ya existe un cliente con ese correo."
_MENSAJE_CONFLICTO_PERFIL = "El cliente ya tiene un perfil."


def _consulta_cliente() -> Select:
    """Arma la consulta base del cliente con su perfil cargado."""
    return select(Cliente).options(joinedload(Cliente.perfil))


async def crear_cliente(
    session: AsyncSession, datos: ClienteCreate
) -> ClienteRead:
    """Inserta un cliente y devuelve su contrato con `perfil=None`."""
    cliente = Cliente(**datos.model_dump())
    session.add(cliente)
    await confirmar(session, _MENSAJE_CONFLICTO_EMAIL)
    return ClienteRead(
        id=cliente.id,
        nombre=cliente.nombre,
        email=cliente.email,
        perfil=None,
    )


async def obtener_cliente(session: AsyncSession, cliente_id: int) -> Cliente:
    """Busca un cliente con su perfil o lanza `NoEncontrado`."""
    consulta = _consulta_cliente().where(Cliente.id == cliente_id)
    cliente = (await session.execute(consulta)).scalars().first()
    if cliente is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADO)
    return cliente


async def _releer_cliente(session: AsyncSession, cliente_id: int) -> Cliente:
    """Vuelve a leer el cliente forzando el refresco de su perfil."""
    consulta = _consulta_cliente().where(Cliente.id == cliente_id)
    consulta = consulta.execution_options(populate_existing=True)
    cliente = (await session.execute(consulta)).scalars().first()
    if cliente is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADO)
    return cliente


async def actualizar_cliente(
    session: AsyncSession, cliente_id: int, datos: ClienteUpdate
) -> Cliente:
    """Aplica solo los campos enviados y conserva el perfil."""
    cliente = await obtener_cliente(session, cliente_id)
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        return cliente

    cliente.sqlmodel_update(cambios)
    session.add(cliente)
    await confirmar(session, _MENSAJE_CONFLICTO_EMAIL)
    return await _releer_cliente(session, cliente_id)


async def crear_perfil(
    session: AsyncSession, cliente_id: int, datos: PerfilCreate
) -> PerfilCliente:
    """Crea el perfil de un cliente existente.

    La existencia del cliente se resuelve con `404`; el segundo perfil lo
    rechaza la restricción `UNIQUE` y se traduce a `409`.
    """
    cliente = await session.get(Cliente, cliente_id)
    if cliente is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADO)

    perfil = PerfilCliente(cliente_id=cliente_id, **datos.model_dump())
    session.add(perfil)
    await confirmar(session, _MENSAJE_CONFLICTO_PERFIL)
    return perfil


async def listar_ventas_de_cliente(
    session: AsyncSession, cliente_id: int, paginacion: Paginacion
) -> list[Venta]:
    """Devuelve una página de ventas del cliente ordenada por `id`."""
    cliente = await session.get(Cliente, cliente_id)
    if cliente is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADO)

    consulta = (
        select(Venta)
        .where(Venta.cliente_id == cliente_id)
        .order_by(Venta.id)
        .offset(paginacion.offset)
        .limit(paginacion.limit)
    )
    return list((await session.execute(consulta)).scalars().all())
