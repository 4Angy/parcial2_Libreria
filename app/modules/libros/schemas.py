"""DTO de libros.

No se define `LibroCreate`: el alta de libros pertenece al change `04`. El
detalle aplana la autoría como una lista de `LibroAutorRead` y el listado usa
`LibroResumenRead` para no cargar relaciones que no expone.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.autores.schemas import AutorRef
from app.modules.editoriales.schemas import EditorialRef
from app.modules.generos.schemas import GeneroRef


class LibroUpdate(BaseModel):
    """Cuerpo parcial del `PATCH` de un libro.

    `precio` y `stock` validan en el contrato los mismos rangos que la base:
    un valor inválido responde `422` y no llega a la escritura. `genero_id`
    acepta `null` para quitarle el género al libro.
    """

    model_config = ConfigDict(extra="forbid")

    isbn: Optional[str] = None
    titulo: Optional[str] = None
    precio: Optional[Decimal] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    editorial_id: Optional[int] = None
    genero_id: Optional[int] = None


class LibroResumenRead(BaseModel):
    """Libro de un listado: sin autores y con sus referencias."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    editorial: Optional[EditorialRef] = None
    genero: Optional[GeneroRef] = None


class LibroAutorRead(BaseModel):
    """Participación de un autor en un libro."""

    model_config = ConfigDict(from_attributes=True)

    autor: Optional[AutorRef] = None
    rol: str
    orden: int


class LibroRead(LibroResumenRead):
    """Detalle de un libro con la lista de sus autorías."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # La entidad ORM expone `autorias`; el contrato publica `autores` con el
    # rol y el orden de cada participación.
    autores: list[LibroAutorRead] = Field(
        default_factory=list, validation_alias="autorias"
    )


class LibroDeAutorRead(BaseModel):
    """Participación tal como la devuelve el sublistado de un autor."""

    model_config = ConfigDict(from_attributes=True)

    libro: Optional[LibroResumenRead] = None
    rol: str
    orden: int
