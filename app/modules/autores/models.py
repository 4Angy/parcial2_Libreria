"""Modelos de tabla de autores.

El módulo se importa desde `app.core.registry.import_model_modules()` antes de
`create_all`; cualquier script que use estas clases debe llamar primero a esa
función para que SQLAlchemy configure todos los mapeos del dominio.
"""

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import LibroAutor


class Autor(SQLModel, table=True):
    """Autor que participa en uno o más libros a través de sus autorías.

    La navegación hacia los libros pasa por `LibroAutor`, que conserva el rol
    y el orden de cada participación.
    """

    __tablename__ = "autor"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    nacionalidad: Optional[str] = Field(default=None)

    autorias: list["LibroAutor"] = Relationship(back_populates="autor")
