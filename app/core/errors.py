"""Errores de dominio y traducción centralizada de los rechazos de la base.

Los servicios lanzan `NoEncontrado` o `Conflicto` y no conocen códigos HTTP
más allá del que declara la excepción. Toda escritura confirma la transacción
con `confirmar()`, que convierte un `IntegrityError` en `Conflicto` con un
mensaje propio elegido por `SQLSTATE`. El texto original de la base nunca sale
de este módulo.
"""

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

# Mensajes estables por clase de error de integridad. No nombran tablas,
# restricciones ni códigos: solo describen la regla de negocio.
_MENSAJE_REFERENCIA_INEXISTENTE = "La referencia indicada no existe."
_MENSAJE_RANGO_INVALIDO = "Los datos no cumplen una regla de rango."
_MENSAJE_INTEGRIDAD_GENERICO = "La operación viola una restricción de integridad."


class ErrorDeDominio(Exception):
    """Error de negocio con el código HTTP que le corresponde."""

    status_code = 500

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class NoEncontrado(ErrorDeDominio):
    """El recurso de la ruta no existe."""

    status_code = 404


class Conflicto(ErrorDeDominio):
    """La base rechazó la escritura por una restricción."""

    status_code = 409


def _sqlstate(exc: IntegrityError) -> Optional[str]:
    """Extrae el `SQLSTATE` del error original sin exponerlo al cliente.

    El dialecto asincrónico de PostgreSQL conserva el código en `sqlstate`
    (o en `pgcode` en variantes del driver). Si el error no lo trae, se usa el
    mensaje genérico.
    """
    original = exc.orig
    if original is None:
        return None
    codigo = getattr(original, "sqlstate", None)
    if codigo is None:
        codigo = getattr(original, "pgcode", None)
    return codigo


def _mensaje_conflicto(exc: IntegrityError, mensaje_operacion: str) -> str:
    """Elige el mensaje propio según el `SQLSTATE` del rechazo."""
    codigo = _sqlstate(exc)
    if codigo == "23505":
        return mensaje_operacion
    if codigo == "23503":
        return _MENSAJE_REFERENCIA_INEXISTENTE
    if codigo == "23514":
        return _MENSAJE_RANGO_INVALIDO
    return _MENSAJE_INTEGRIDAD_GENERICO


async def confirmar(session: AsyncSession, mensaje_conflicto: str) -> None:
    """Confirma la transacción y traduce `IntegrityError` a `Conflicto`.

    Ante un rechazo de integridad se descarta la transacción fallida con
    `rollback()` y se lanza `Conflicto` desde `None`, de modo que la cadena de
    excepciones original no llegue al handler. Los demás `SQLAlchemyError` se
    propagan para que el handler de `app/main.py` responda `500` genérico.
    """
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise Conflicto(_mensaje_conflicto(exc, mensaje_conflicto)) from None
