"""Comprueba la traducción de `IntegrityError` a `Conflicto`.

El script no necesita la base: usa una sesión falsa que lanza un
`IntegrityError` con el `SQLSTATE` indicado. Verifica el código, el mensaje
propio de cada caso, el `rollback()` y que ningún mensaje filtre texto de la
base. También comprueba que un `SQLAlchemyError` que no es de integridad se
re-lanza para el handler `500`.

Uso:
    .venv\\Scripts\\python.exe test\\errores_integridad.py

Imprime `ok` y termina con código 0 si todas las comprobaciones pasan.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Permite ejecutar el archivo directamente sin depender de PYTHONPATH.
_RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

from sqlalchemy.exc import IntegrityError, SQLAlchemyError  # noqa: E402

from app.core.errors import Conflicto, confirmar  # noqa: E402

# Fragmentos que jamás deben aparecer en un mensaje de la API.
_PROHIBIDOS = (
    "23505",
    "23503",
    "23514",
    "_key",
    "duplicate key",
    "editorial_nombre_key",
    "perfil_cliente",
    "INSERT",
    "SELECT",
    "Traceback",
)

_MENSAJE_OPERACION = "Ya existe una editorial con ese nombre."


class _ErrorOriginal(Exception):
    """Imita el error del driver conservando el `SQLSTATE`."""

    def __init__(self, sqlstate: str) -> None:
        super().__init__(
            'duplicate key value violates unique constraint "editorial_nombre_key"'
        )
        self.sqlstate = sqlstate


class _SesionFalsa:
    """Sesión mínima que registra `rollback()` y lanza el error configurado."""

    def __init__(self, error: Optional[Exception] = None) -> None:
        self._error = error
        self.rollbacks = 0

    async def commit(self) -> None:
        if self._error is not None:
            raise self._error

    async def rollback(self) -> None:
        self.rollbacks += 1


def _integrity_error(sqlstate: str) -> IntegrityError:
    """Construye un `IntegrityError` con el `SQLSTATE` pedido."""
    return IntegrityError(
        "INSERT INTO editorial (nombre) VALUES ($1)",
        {},
        _ErrorOriginal(sqlstate),
    )


async def _comprobar_conflicto(
    sqlstate: str, mensaje_esperado: str
) -> None:
    """Verifica código, mensaje, rollback y ausencia de texto interno."""
    sesion = _SesionFalsa(_integrity_error(sqlstate))
    try:
        await confirmar(sesion, _MENSAJE_OPERACION)
    except Conflicto as exc:
        assert exc.status_code == 409, f"Se esperaba 409 y llegó {exc.status_code}."
        assert exc.mensaje == mensaje_esperado, (
            f"Mensaje inesperado para {sqlstate}: {exc.mensaje!r}"
        )
        assert sesion.rollbacks == 1, "El rechazo debe hacer rollback()."
        for prohibido in _PROHIBIDOS:
            assert prohibido not in exc.mensaje, (
                f"El mensaje filtra {prohibido!r}: {exc.mensaje!r}"
            )
    else:
        raise AssertionError(f"{sqlstate} debía traducirse a Conflicto.")


async def main() -> None:
    """Ejecuta los cuatro SQLSTATE, el error no de integridad y el éxito."""
    await _comprobar_conflicto("23505", _MENSAJE_OPERACION)
    await _comprobar_conflicto("23503", "La referencia indicada no existe.")
    await _comprobar_conflicto(
        "23514", "Los datos no cumplen una regla de rango."
    )
    await _comprobar_conflicto(
        "23000", "La operación viola una restricción de integridad."
    )

    # Un error que no es de integridad se propaga al handler de 500.
    sesion = _SesionFalsa(SQLAlchemyError("falla de conexión"))
    try:
        await confirmar(sesion, _MENSAJE_OPERACION)
    except SQLAlchemyError:
        pass
    else:
        raise AssertionError("Un SQLAlchemyError no debe convertirse en 409.")

    # Un commit exitoso no hace rollback.
    sesion = _SesionFalsa(None)
    await confirmar(sesion, _MENSAJE_OPERACION)
    assert sesion.rollbacks == 0, "Un commit exitoso no debe hacer rollback()."


if __name__ == "__main__":
    asyncio.run(main())
    print("ok")
