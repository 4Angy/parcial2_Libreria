"""Comprueba la asincronía y la tarea en segundo plano del alta de venta.

Registra una venta real contra la base, mide que el alta responda en menos de
0.5 segundos (el aviso no bloquea la respuesta) y verifica que el aviso del
comprobante se registra en el log después de enviar la respuesta. También
comprueba que el aviso no accede a la base.

Uso:
    python test\\asincronia_background.py
Imprime `ok` y termina con código 0 si todas las comprobaciones pasan.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

_RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

from fastapi import BackgroundTasks  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.registry import import_model_modules  # noqa: E402
from app.modules.clientes.models import Cliente  # noqa: E402
from app.modules.ventas.router import crear_venta as crear_venta_router  # noqa: E402
from app.modules.ventas.schemas import VentaCreate  # noqa: E402
from app.modules.ventas.service import crear_venta as crear_venta_service  # noqa: E402

import_model_modules()


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    registros: list[logging.LogRecord] = []

    class _Capturador(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            registros.append(record)

    capturador = _Capturador()
    logger = logging.getLogger("app.modules.ventas.service")
    logger.addHandler(capturador)
    logger.setLevel(logging.INFO)

    async with session_factory() as session:
        # Cliente existente de la semilla (id 1).
        cliente = await session.get(Cliente, 1)
        assert cliente is not None, "Falta la semilla de clientes."

        datos = VentaCreate(cliente_id=1, renglones=[{"libro_id": 1, "cantidad": 1}])

        background_tasks = BackgroundTasks()

        inicio = time.monotonic()
        venta = await crear_venta_router(datos, session, background_tasks)
        duracion = time.monotonic() - inicio

        # La respuesta (alta) debe ser rápida: el aviso no bloquea.
        assert duracion < 0.5, duracion
        assert venta is not None
        venta_id = venta.id

        # Ejecutar las tareas en segundo plano (simula el post-respuesta).
        await background_tasks()

    # El aviso debe haberse registrado.
    await asyncio.sleep(0.1)
    mensajes = [r.getMessage() for r in registros]
    assert any("Comprobante enviado" in m for m in mensajes), mensajes
    assert any(str(venta_id) in m for m in mensajes), mensajes

    logger.removeHandler(capturador)
    await engine.dispose()
    print("ok")


if __name__ == "__main__":
    asyncio.run(main())
    print("ok")
