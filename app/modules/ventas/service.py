"""Reglas de negocio de ventas.

El detalle carga el cliente y los renglones con su libro para que la
serialización no dependa de la carga perezosa. El alta lee los libros en una
sola consulta para copiar el precio, calcula el total en el servidor y relee el
detalle con `populate_existing` antes de responder.
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Select
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import Conflicto, NoEncontrado, confirmar
from app.core.pagination import Paginacion
from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import VentaCreate

_MENSAJE_NO_ENCONTRADA = "La venta no existe."
_MENSAJE_LIBRO_INEXISTENTE = "El libro indicado no existe."
_MENSAJE_CONFLICTO = "La venta no se pudo registrar."
_CENTAVOS = Decimal("0.01")

_logger = logging.getLogger(__name__)


def _consulta_venta() -> Select:
    """Arma la consulta base del detalle con cliente y renglones cargados."""
    return select(Venta).options(
        joinedload(Venta.cliente),
        selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
    )


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
    consulta = _consulta_venta().where(Venta.id == venta_id)
    venta = (await session.execute(consulta)).scalars().first()
    if venta is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADA)
    return venta


async def _releer_venta(session: AsyncSession, venta_id: int) -> Venta:
    """Vuelve a leer el detalle forzando el refresco de sus relaciones.

    Con `expire_on_commit=False` la venta conserva los renglones asignados en
    memoria; `populate_existing` los reemplaza por las filas de la base para
    que el título y el subtotal salgan de la lectura final.
    """
    consulta = _consulta_venta().where(Venta.id == venta_id)
    consulta = consulta.execution_options(populate_existing=True)
    venta = (await session.execute(consulta)).scalars().first()
    if venta is None:
        raise NoEncontrado(_MENSAJE_NO_ENCONTRADA)
    return venta


async def crear_venta(session: AsyncSession, datos: VentaCreate) -> Venta:
    """Registra una venta con sus renglones y devuelve el detalle releído.

    La lectura de los libros es la que RN-06 exige para copiar el precio, no
    una comprobación previa de existencia: se hace con una sola consulta `IN`
    y un `libro_id` ausente se traduce a `409` con un mensaje propio. El
    renglón se construye con `libro_id` y sin asignar la relación `libro`, para
    no disparar un `SELECT` por libro.
    """
    ids = [renglon.libro_id for renglon in datos.renglones]
    libros = {
        libro.id: libro
        for libro in (
            await session.execute(select(Libro).where(Libro.id.in_(ids)))
        )
        .scalars()
        .all()
    }
    if any(libro_id not in libros for libro_id in ids):
        raise Conflicto(_MENSAJE_LIBRO_INEXISTENTE)

    renglones = [
        RenglonVenta(
            libro_id=renglon.libro_id,
            cantidad=renglon.cantidad,
            precio_unitario=libros[renglon.libro_id].precio,
        )
        for renglon in datos.renglones
    ]
    total = sum(
        (renglon.precio_unitario * renglon.cantidad for renglon in renglones),
        Decimal("0"),
    ).quantize(_CENTAVOS)
    venta = Venta(
        cliente_id=datos.cliente_id,
        fecha=datetime.now(timezone.utc),
        total=total,
    )
    venta.renglones = renglones
    session.add(venta)
    await confirmar(session, _MENSAJE_CONFLICTO)
    return await _releer_venta(session, venta.id)


async def avisar_comprobante(cliente_id: int, venta_id: int) -> None:
    """Avisa al cliente del comprobante de su venta en segundo plano.

    Corre después de enviar la respuesta del `POST /ventas/`: no bloquea al
    servidor y no accede a la base, porque la sesión de la petición ya se
    cerró. Cualquier error se registra y no se propaga, para no afectar a
    otras tareas agendadas.
    """
    try:
        await asyncio.sleep(0.5)
        _logger.info(
            "Comprobante enviado al cliente %s por la venta %s.",
            cliente_id,
            venta_id,
        )
    except Exception:  # noqa: BLE001
        _logger.exception(
            "Falló el aviso del comprobante para la venta %s del cliente %s.",
            venta_id,
            cliente_id,
        )
