"""DTO de géneros.

El género solo tiene alta y lectura: la tabla de endpoints no define `PATCH`.
"""

from pydantic import BaseModel, ConfigDict


class GeneroCreate(BaseModel):
    """Cuerpo del alta de un género."""

    model_config = ConfigDict(extra="forbid")

    nombre: str


class GeneroRead(BaseModel):
    """Género tal como lo devuelve la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class GeneroRef(BaseModel):
    """Referencia mínima de un género dentro de otro recurso."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
