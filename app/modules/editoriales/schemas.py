"""DTO de editoriales.

`EditorialCreate` no declara `id` y rechaza campos ajenos al contrato;
`EditorialUpdate` permite enviar solo los campos que se quieren cambiar y
`EditorialRead` se valida desde la entidad ORM.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class EditorialCreate(BaseModel):
    """Cuerpo del alta de una editorial."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    pais: Optional[str] = None


class EditorialUpdate(BaseModel):
    """Cuerpo parcial del `PATCH` de una editorial."""

    model_config = ConfigDict(extra="forbid")

    nombre: Optional[str] = None
    pais: Optional[str] = None


class EditorialRead(BaseModel):
    """Editorial tal como la devuelve la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    pais: Optional[str] = None


class EditorialRef(BaseModel):
    """Referencia mínima de una editorial dentro de otro recurso."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
