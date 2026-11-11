"""Configuración de la aplicación leída del entorno.

Carga el archivo `.env` con `python-dotenv` y expone `get_settings()`, que
valida las variables obligatorias y cachea el resultado para no releer el
entorno en cada llamada.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

# Valores que se interpretan como verdaderos en las variables booleanas.
_VALORES_VERDADEROS = frozenset({"1", "true", "yes", "on", "si", "sí"})

# Prefijo obligatorio: el motor es asincrónico y habla con PostgreSQL.
_DRIVER_REQUERIDO = "postgresql+asyncpg://"


@dataclass(frozen=True)
class Settings:
    """Configuración inmutable del proceso."""

    database_url: str
    sql_echo: bool


def _leer_booleano(nombre: str) -> bool:
    """Interpreta una variable booleana; ausente o no reconocida es `False`."""
    valor = os.environ.get(nombre, "")
    return valor.strip().lower() in _VALORES_VERDADEROS


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la configuración validada del proceso.

    `DATABASE_URL` no tiene valor por defecto: si falta, está vacía o no usa
    el driver asincrónico de PostgreSQL, se lanza `RuntimeError` y el arranque
    termina antes de abrir cualquier conexión. El mensaje de error nombra la
    variable y nunca incluye credenciales.
    """
    load_dotenv()

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError(
            "Falta la variable de entorno DATABASE_URL. Definila en el entorno "
            "o en el archivo .env con la forma "
            "postgresql+asyncpg://<usuario>:<contrasena>@<host>:<puerto>/<base>."
        )
    if not database_url.startswith(_DRIVER_REQUERIDO):
        raise RuntimeError(
            "La variable DATABASE_URL debe usar el driver asincrónico "
            "'postgresql+asyncpg'. Revisá su valor en el entorno o en .env."
        )

    return Settings(
        database_url=database_url,
        sql_echo=_leer_booleano("SQL_ECHO"),
    )
