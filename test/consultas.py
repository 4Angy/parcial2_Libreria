"""Comprueba la búsqueda ligada y la carga anticipada contra la base real.

Registra las sentencias del motor, ejecuta `listar_libros` con el texto de
C-08 y afirma que el patrón viaja como parámetro y no dentro del SQL. Después
lee un libro y una venta, cierra la sesión y serializa sus DTO para demostrar
que las relaciones se cargaron de antemano.

Uso:
    .venv\\Scripts\\python.exe test\\consultas.py

Imprime `ok` y termina con código 0 si todas las comprobaciones pasan.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

# Permite ejecutar el archivo directamente sin depender de PYTHONPATH.
_RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

from sqlalchemy import event  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.pagination import Paginacion  # noqa: E402
from app.core.registry import import_model_modules  # noqa: E402
from app.modules.libros.schemas import LibroRead  # noqa: E402
from app.modules.libros.service import listar_libros, obtener_libro  # noqa: E402
from app.modules.ventas.schemas import VentaRead  # noqa: E402
from app.modules.ventas.service import obtener_venta  # noqa: E402

_INYECCION = "' OR '1'='1"


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


async def main() -> None:
    """Ejecuta la búsqueda, las dos lecturas y la serialización posterior."""
    import_model_modules()
    settings = get_settings()

    engine = create_async_engine(settings.database_url)
    registro: list[tuple[str, Any]] = []
    _registrar_sentencias(engine, registro)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    libro = None
    venta = None
    try:
        async with session_factory() as session:
            libros = await listar_libros(
                session, Paginacion(limit=20, offset=0), _INYECCION, None
            )
            assert libros == [], "El texto de inyección no debe encontrar filas."

            sentencia, parametros = registro[-1]
            print("Sentencia:", sentencia)
            print("Parámetros:", parametros)
            assert "ILIKE $" in sentencia, sentencia
            assert _INYECCION not in sentencia, sentencia
            assert _INYECCION in repr(parametros), parametros

            libro = await obtener_libro(session, 1)
            venta = await obtener_venta(session, 1)
    finally:
        await engine.dispose()

    # La sesión y el motor ya están cerrados: si faltara una relación, la
    # serialización fallaría por carga perezosa.
    assert libro is not None
    datos_libro = LibroRead.model_validate(libro).model_dump(mode="json")
    assert datos_libro["editorial"]["id"] == libro.editorial_id
    assert datos_libro["genero"] is not None
    assert datos_libro["autores"], "El detalle debe incluir sus autores."
    assert datos_libro["autores"][0]["rol"] == "autor"

    assert venta is not None
    datos_venta = VentaRead.model_validate(venta).model_dump(mode="json")
    assert datos_venta["cliente"]["id"] == venta.cliente_id
    assert len(datos_venta["renglones"]) == 2
    assert all("subtotal" in renglon for renglon in datos_venta["renglones"])
    assert datos_venta["fecha"].endswith("Z")


if __name__ == "__main__":
    asyncio.run(main())
    print("ok")
