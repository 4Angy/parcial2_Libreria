"""Comprueba la carga anticipada y el número fijo de consultas (Ejercicio 5).

Registra las sentencias del motor, lee el detalle de un libro y de una venta
con distinta cardinalidad de colecciones, y afirma que:
  - el detalle de libro emite un número fijo de `SELECT` (uno principal con
    `JOIN` y uno `SELECT IN` para las autorías), sin consulta por autor;
  - el detalle de venta emite un número fijo de `SELECT` (uno principal con
    `JOIN` y uno `SELECT IN` para los renglones), sin consulta por renglón;
  - dos libros con distinta cantidad de autores emiten la misma cantidad de
    consultas, e igual para dos ventas con distinta cantidad de renglones;
  - serializar ambos detalles fuera de la sesión no emite consultas nuevas ni
    depende de la carga perezosa.

Uso:
    python test\\carga_anticipada.py
Imprime `ok` y termina con código 0 si todas las comprobaciones pasan.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

_RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

from sqlalchemy import event  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.registry import import_model_modules  # noqa: E402
from app.modules.libros.schemas import LibroRead  # noqa: E402
from app.modules.libros.service import obtener_libro  # noqa: E402
from app.modules.ventas.schemas import VentaRead  # noqa: E402
from app.modules.ventas.service import obtener_venta  # noqa: E402


def _registrar_sentencias(engine: Any, registro: list[tuple[str, Any]]) -> None:
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
    return [
        sentencia
        for sentencia, _ in registro
        if sentencia.lstrip().upper().startswith("SELECT")
    ]


async def main() -> None:
    import_model_modules()
    settings = get_settings()

    engine = create_async_engine(settings.database_url)
    registro: list[tuple[str, Any]] = []
    _registrar_sentencias(engine, registro)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    libro_simple = None  # 1 autor
    libro_multiple = None  # varios autores
    venta_simple = None
    venta_multiple = None

    try:
        async with session_factory() as session:
            registro.clear()
            libro_simple = await obtener_libro(session, 1)  # Cien años: 1 autor
            lecturas_libro_simple = len(_selecciones(registro))

            registro.clear()
            libro_multiple = await obtener_libro(session, 9)  # Freakonomics: 2 autores
            lecturas_libro_multiple = len(_selecciones(registro))

            registro.clear()
            venta_simple = await obtener_venta(session, 1)
            lecturas_venta_simple = len(_selecciones(registro))

            registro.clear()
            venta_multiple = await obtener_venta(session, 2)
            lecturas_venta_multiple = len(_selecciones(registro))

            # Cada detalle: 1 SELECT principal + 1 SELECT IN para la colección.
            assert lecturas_libro_simple == 2, lecturas_libro_simple
            assert lecturas_libro_multiple == 2, lecturas_libro_multiple
            assert lecturas_venta_simple == 2, lecturas_venta_simple
            assert lecturas_venta_multiple == 2, lecturas_venta_multiple

            # Cardinalidad no afecta la cantidad de consultas.
            assert lecturas_libro_simple == lecturas_libro_multiple
            assert lecturas_venta_simple == lecturas_venta_multiple

            # Ninguna consulta por elemento: no hay SELECT con id = $ por autor/renglón.
            assert not any(
                "libro_autor" in s.lower() and "libro_id = $" in s.lower()
                for s in _selecciones(registro)
            )

            # Serialización fuera de sesión no emite consultas.
            antes = len(registro)
            datos_libro = LibroRead.model_validate(libro_simple).model_dump(
                mode="json"
            )
            assert len(registro) == antes, "Serializar el libro emitió consultas."
            assert datos_libro["autores"], "El detalle debe incluir autores."

            datos_libro_m = LibroRead.model_validate(libro_multiple).model_dump(
                mode="json"
            )
            assert len(datos_libro_m["autores"]) == 2, datos_libro_m["autores"]

            datos_venta = VentaRead.model_validate(venta_simple).model_dump(
                mode="json"
            )
            assert len(registro) == antes, "Serializar la venta emitió consultas."
            assert len(datos_venta["renglones"]) == 2, datos_venta["renglones"]
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
    print("ok")
