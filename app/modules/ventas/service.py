"""Reglas de negocio de ventas.

El change `03` solo expone lecturas: no hay funciones de escritura. El detalle
carga el cliente y los renglones con su libro para que la serialización no
dependa de la carga perezosa.
"""

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import NoEncontrado
from app.core.pagination import Paginacion
from app.modules.ventas.models import RenglonVenta, Venta

_MENSAJE_NO_ENCONTRADA = "La venta no existe."


async def listar_ventas(
    session: AsyncSession, paginacion: Paginacion
) -> list[Venta]:
    """Devuelve una página de ventas ordenada por `id`."""
    consulta = (
        select(Venta)
        .order_by(Venta.id)
        .offset(paginacion.offset)
        .limit(paginacion.limit)
    )
    return list((await session.execute(consulta)).scalars().all())


async def obtener_venta(session: AsyncSession, venta_id: int) -> Venta:
    """Busca una venta con cliente y renglones o lanza `NoEncontrado`."""
    consulta = (
        select(Venta)
        .options(
            joinedload(Venta.cliente),
            selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
        )
        .where(Venta.id == venta_id)
    )
    venta = (await session.execute(consulta)).scalars().first()
    if venta is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADA)
    return venta
