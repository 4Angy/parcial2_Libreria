"""Modelos de tabla de libros y de sus autorías.

El módulo se importa desde `app.core.registry.import_model_modules()` antes de
`create_all`; cualquier script que use estas clases debe llamar primero a esa
función para que SQLAlchemy configure todos los mapeos del dominio.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero
    from app.modules.ventas.models import RenglonVenta


class Libro(SQLModel, table=True):
    """Libro del catálogo con su precio exacto y su stock disponible.

    `precio` se declara con `Numeric(10, 2)` mediante `sa_column` para que el
    tipo quede fijo en el modelo y no dependa de la versión de SQLModel
    resuelta. Los rangos de precio y stock viven en la base como `CHECK`
    nombrados.
    """

    __tablename__ = "libro"
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_libro_precio_positivo"),
        CheckConstraint("stock >= 0", name="ck_libro_stock_no_negativo"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    isbn: str = Field(unique=True)
    titulo: str
    precio: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    stock: int
    editorial_id: int = Field(foreign_key="editorial.id", index=True)
    genero_id: Optional[int] = Field(default=None, foreign_key="genero.id", index=True)

    editorial: Optional["Editorial"] = Relationship(
        back_populates="libros", sa_relationship_kwargs={"lazy": "raise"}
    )
    genero: Optional["Genero"] = Relationship(
        back_populates="libros", sa_relationship_kwargs={"lazy": "raise"}
    )
    autorias: list["LibroAutor"] = Relationship(
        back_populates="libro", sa_relationship_kwargs={"lazy": "raise"}
    )
    renglones: list["RenglonVenta"] = Relationship(
        back_populates="libro", sa_relationship_kwargs={"lazy": "raise"}
    )


class LibroAutor(SQLModel, table=True):
    """Autoría de un libro: entidad con clave compuesta, rol y orden.

    No se usa una tabla de enlace sin clase porque ese mecanismo esconde los
    atributos propios de la relación (`rol` y `orden`). La clave primaria es
    `(libro_id, autor_id)` y `autor_id` lleva índice explícito porque
    PostgreSQL no indexa claves foráneas por sí solo.
    """

    __tablename__ = "libro_autor"
    __table_args__ = (
        CheckConstraint("orden >= 1", name="ck_libro_autor_orden_positivo"),
        CheckConstraint(
            "rol IN ('autor', 'coautor', 'traductor', 'ilustrador')",
            name="ck_libro_autor_rol_valido",
        ),
    )

    libro_id: int = Field(foreign_key="libro.id", primary_key=True)
    autor_id: int = Field(foreign_key="autor.id", primary_key=True, index=True)
    rol: str
    orden: int

    libro: Optional["Libro"] = Relationship(
        back_populates="autorias", sa_relationship_kwargs={"lazy": "raise"}
    )
    autor: Optional["Autor"] = Relationship(
        back_populates="autorias", sa_relationship_kwargs={"lazy": "raise"}
    )
