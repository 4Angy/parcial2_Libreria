"""Modelos de tabla de editoriales.

El módulo se importa desde `app.core.registry.import_model_modules()` antes de
`create_all`; cualquier script que use estas clases debe llamar primero a esa
función para que SQLAlchemy configure todos los mapeos del dominio.
"""

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import Libro


class Editorial(SQLModel, table=True):
    """Editorial que publica libros del catálogo.

    El nombre de tabla es explícito porque la heurística de SQLModel deriva
    nombres en minúsculas sin separador y el esquema del dominio exige
    `editorial`, `libro_autor` y `renglon_venta`.
    """

    __tablename__ = "editorial"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)
    pais: Optional[str] = Field(default=None)

    libros: list["Libro"] = Relationship(
        back_populates="editorial", sa_relationship_kwargs={"lazy": "raise"}
    )
