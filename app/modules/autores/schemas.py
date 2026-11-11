"""DTO de autores."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class AutorCreate(BaseModel):
    """Cuerpo del alta de un autor."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    nacionalidad: Optional[str] = None


class AutorUpdate(BaseModel):
    """Cuerpo parcial del `PATCH` de un autor."""

    model_config = ConfigDict(extra="forbid")

    nombre: Optional[str] = None
    nacionalidad: Optional[str] = None


class AutorRead(BaseModel):
    """Autor tal como lo devuelve la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    nacionalidad: Optional[str] = None


class AutorRef(BaseModel):
    """Referencia mínima de un autor dentro de otro recurso."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
