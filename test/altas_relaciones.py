"""Demuestra las relaciones del alta de venta contra la base real.

Registra las sentencias con `before_cursor_execute`, crea un cliente `Prueba 04`
y una venta con dos renglones llamando a `crear_venta`. Comprueba que el total
es la suma de `cantidad * libro.precio` leída de la base, que cada
`precio_unitario` coincide con el precio del libro, que la lectura de los libros
es una sola consulta `IN` y que serializar la respuesta no emite consultas
nuevas. Después cambia el precio del libro con un `UPDATE`, relee la venta en
una sesión nueva y comprueba que el precio copiado y el total no cambian;
restaura el precio original en un `finally` y limpia sus filas.

Uso:
    .venv\\Scripts\\python.exe test\\altas_relaciones.py

Imprime las sentencias del alta, el total esperado y `ok`, y termina con
código 0 si todas las comprobaciones pasan.
"""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

# Permite ejecutar el archivo directamente sin depender de PYTHONPATH.
_RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

from sqlalchemy import delete, event, update  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlmodel import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.registry import import_model_modules  # noqa: E402
from app.modules.clientes.models import Cliente  # noqa: E402
from app.modules.libros.models import Libro  # noqa: E402
from app.modules.ventas.models import RenglonVenta, Venta  # noqa: E402
from app.modules.ventas.schemas import VentaCreate, VentaRead  # noqa: E402
from app.modules.ventas.service import crear_venta, obtener_venta  # noqa: E402

_CENTAVOS = Decimal("0.01")
_PREFIJO = "Prueba 04"


def _registrar_sentencias(engine: Any, registro: list[tuple[str, Any]]) -> None:
    """Anexa cada sentencia ejecutada con sus parámetros ligados."""

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def _guardar(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        registro.append((statement, parameters))


def _selecciones(registro: list[tuple[str, Any]]) -> list[str]:
    """Filtra las sentencias que son lecturas."""
    return [
        sentencia
        for sentencia, _ in registro
        if sentencia.lstrip().upper().startswith("SELECT")
    ]


async def _leer_renglones(
    session: Any, venta_id: int
) -> list[RenglonVenta]:
    """Lee los renglones guardados de una venta."""
    consulta = select(RenglonVenta).where(RenglonVenta.venta_id == venta_id)
    return list((await session.execute(consulta)).scalars().all())


async def main() -> None:
    """Ejecuta el alta, la comprobación de precios y el cambio posterior."""
    import_model_modules()
    settings = get_settings()

    engine = create_async_engine(settings.database_url)
    registro: list[tuple[str, Any]] = []
    _registrar_sentencias(engine, registro)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    cliente_id = None
    venta_id = None
    libro_id = None
    precio_original = None
    try:
        async with session_factory() as session:
            cliente = Cliente(
                nombre=f"{_PREFIJO} Cliente Relaciones",
                email="prueba04-relaciones@example.com",
            )
            session.add(cliente)
            await session.commit()
            cliente_id = cliente.id

            libros = list(
                (
                    await session.execute(
                        select(Libro).order_by(Libro.id).limit(2)
                    )
                )
                .scalars()
                .all()
            )
            assert len(libros) == 2, "La semilla debe tener al menos dos libros."
            primero, segundo = libros
            libro_id = primero.id
            precio_original = primero.precio
            cantidades = {primero.id: 2, segundo.id: 1}
            esperado = (
                primero.precio * cantidades[primero.id]
                + segundo.precio * cantidades[segundo.id]
            ).quantize(_CENTAVOS)

            registro.clear()
            datos = VentaCreate(
                cliente_id=cliente_id,
                renglones=[
                    {"libro_id": primero.id, "cantidad": cantidades[primero.id]},
                    {"libro_id": segundo.id, "cantidad": cantidades[segundo.id]},
                ],
            )
            venta = await crear_venta(session, datos)
            venta_id = venta.id

            sentencias_alta = list(registro)
            for sentencia, parametros in sentencias_alta:
                print("SQL:", " ".join(sentencia.split()))
                print("Parámetros:", parametros)
            print("Total esperado:", esperado)

            lecturas = _selecciones(sentencias_alta)
            assert len(lecturas) == 3, (
                "El alta debe leer los libros una vez y el detalle dos veces; "
                f"se observaron {len(lecturas)} lecturas."
            )
            lecturas_de_libros = [
                sentencia
                for sentencia in lecturas
                if "FROM libro" in sentencia and "renglon_venta" not in sentencia
            ]
            assert len(lecturas_de_libros) == 1, (
                "Los libros deben leerse con una sola consulta IN: "
                f"{lecturas_de_libros}"
            )
            assert "IN" in lecturas_de_libros[0].upper(), lecturas_de_libros[0]
            assert not any(
                "libro.id = $" in sentencia for sentencia in lecturas
            ), "No debe haber una lectura por renglón."

            # La serialización ocurre después de la lectura final: no debe
            # emitir ninguna consulta nueva.
            antes = len(registro)
            datos_venta = VentaRead.model_validate(venta).model_dump(mode="json")
            assert len(registro) == antes, (
                "Serializar la respuesta no debe emitir consultas."
            )

            assert Decimal(datos_venta["total"]) == esperado, datos_venta["total"]
            assert datos_venta["fecha"].endswith("Z"), datos_venta["fecha"]
            assert len(datos_venta["renglones"]) == 2, datos_venta["renglones"]

            renglones = await _leer_renglones(session, venta_id)
            assert len(renglones) == 2
            total_base = Decimal("0")
            for renglon in renglones:
                libro = (
                    await session.execute(
                        select(Libro).where(Libro.id == renglon.libro_id)
                    )
                ).scalars().first()
                assert libro is not None
                assert renglon.precio_unitario == libro.precio, (
                    f"El renglón de {libro.titulo} copió "
                    f"{renglon.precio_unitario} y el libro vale {libro.precio}."
                )
                assert renglon.cantidad == cantidades[renglon.libro_id]
                total_base += renglon.precio_unitario * renglon.cantidad
            assert total_base.quantize(_CENTAVOS) == esperado, (
                f"El total de la base es {total_base} y se esperaba {esperado}."
            )

            # Cambiar el precio del libro no altera la venta ya registrada.
            nuevo_precio = (precio_original + Decimal("1000.00")).quantize(
                _CENTAVOS
            )
            await session.execute(
                update(Libro)
                .where(Libro.id == libro_id)
                .values(precio=nuevo_precio)
            )
            await session.commit()

        async with session_factory() as otra_sesion:
            venta_releida = await obtener_venta(otra_sesion, venta_id)
            datos_releidos = VentaRead.model_validate(
                venta_releida
            ).model_dump(mode="json")

        assert Decimal(datos_releidos["total"]) == esperado, (
            "El total cambió después de modificar el precio del libro."
        )
        precios_copiados = {
            renglon["libro_id"]: Decimal(renglon["precio_unitario"])
            for renglon in datos_releidos["renglones"]
        }
        assert precios_copiados[primero.id] == precio_original
        assert precios_copiados[segundo.id] == segundo.precio
        assert precios_copiados[primero.id] != nuevo_precio
    finally:
        async with session_factory() as session:
            if libro_id is not None and precio_original is not None:
                await session.execute(
                    update(Libro)
                    .where(Libro.id == libro_id)
                    .values(precio=precio_original)
                )
            if venta_id is not None:
                await session.execute(
                    delete(RenglonVenta).where(
                        RenglonVenta.venta_id == venta_id
                    )
                )
                await session.execute(delete(Venta).where(Venta.id == venta_id))
            if cliente_id is not None:
                await session.execute(
                    delete(Cliente).where(Cliente.id == cliente_id)
                )
            await session.commit()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
    print("ok")
