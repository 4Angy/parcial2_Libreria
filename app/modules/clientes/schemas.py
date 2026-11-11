"""DTO de clientes y de sus perfiles."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class ClienteCreate(BaseModel):
    """Cuerpo del alta de un cliente."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    email: str


class ClienteUpdate(BaseModel):
    """Cuerpo parcial del `PATCH` de un cliente."""

    model_config = ConfigDict(extra="forbid")

    nombre: Optional[str] = None
    email: Optional[str] = None


class PerfilCreate(BaseModel):
    """Cuerpo del alta de un perfil.

    No declara `cliente_id`: el vínculo se toma de la ruta y un cuerpo que
    intente enviarlo responde `422`.
    """

    model_config = ConfigDict(extra="forbid")

    telefono: Optional[str] = None
    direccion: Optional[str] = None


class PerfilRead(BaseModel):
    """Perfil de contacto de un cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    telefono: Optional[str] = None
    direccion: Optional[str] = None


class ClienteRead(BaseModel):
    """Cliente con su perfil como objeto o `null`, nunca como lista."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    perfil: Optional[PerfilRead] = None


class ClienteRef(BaseModel):
    """Referencia mínima de un cliente dentro de otro recurso."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
