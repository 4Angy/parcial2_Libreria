"""DTO de libros.

`LibroCreate` recibe los ids de la editorial, del género y de los autores que
ya existen, más los datos propios de cada autoría (`rol` y `orden`). El detalle
aplana la autoría como una lista de `LibroAutorRead` y el listado usa
`LibroResumenRead` para no cargar relaciones que no expone.
"""

from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class LibroAutorCreate(BaseModel):
    """Autoría que viaja en el alta de un libro.

    Solo lleva el `autor_id`: el autor ya existe y su clave foránea es la que
    rechaza una referencia inexistente. El `rol` reproduce el `CHECK` de la
    base y el `orden` es la posición de la autoría en la tapa.
    """

    model_config = ConfigDict(extra="forbid")

    autor_id: int
    rol: Literal["autor", "coautor", "traductor", "ilustrador"]
    orden: int = Field(ge=1)


class LibroCreate(BaseModel):
    """Cuerpo del alta de un libro con sus autorías.

    `autores` es obligatorio pero acepta la lista vacía: la consigna no exige
    al menos un autor. Las autorías se validan antes de tocar la base para que
    un `autor_id` o un `orden` repetido responda `422` y no un `409` confuso.
    """

    model_config = ConfigDict(extra="forbid")

    isbn: str
    titulo: str
    precio: Decimal = Field(gt=0)
    stock: int = Field(ge=0)
    editorial_id: int
    genero_id: Optional[int] = None
    autores: list[LibroAutorCreate]

    @model_validator(mode="after")
    def _validar_autorias(self) -> "LibroCreate":
        """Rechaza un autor o un orden repetido dentro de la misma alta."""
        autores = [autoria.autor_id for autoria in self.autores]
        if len(autores) != len(set(autores)):
            raise ValueError("No se puede repetir un autor en la misma alta.")
        ordenes = [autoria.orden for autoria in self.autores]
        if len(ordenes) != len(set(ordenes)):
            raise ValueError(
                "No se puede repetir el orden de una autoría en la misma alta."
            )
        return self


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
