"""Paginación reutilizable para todos los listados de la API.

`Paginacion` transporta los dos parámetros ya validados y la dependencia
`paginacion` declara los límites de RN-10. FastAPI valida `limit` y `offset`
antes de ejecutar el handler, de modo que un valor fuera de rango responde
`422` sin llegar a la base.
"""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Query


@dataclass(frozen=True)
class Paginacion:
    """Ventana de filas solicitada por el cliente."""

    limit: int
    offset: int


def paginacion(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Paginacion:
    """Devuelve la ventana validada con los valores por defecto del contrato."""
    return Paginacion(limit=limit, offset=offset)
