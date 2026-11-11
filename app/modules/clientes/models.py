"""Modelos de tabla de clientes y de sus perfiles.

El módulo se importa desde `app.core.registry.import_model_modules()` antes de
`create_all`; cualquier script que use estas clases debe llamar primero a esa
función para que SQLAlchemy configure todos los mapeos del dominio.
"""

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.ventas.models import Venta


class Cliente(SQLModel, table=True):
    """Cliente del sistema, identificado por su correo electrónico único."""

    __tablename__ = "cliente"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(unique=True)

    # La clave foránea vive en `perfil_cliente`, así que SQLAlchemy deduciría
    # una colección; `uselist: False` refleja la cardinalidad uno a uno.
    perfil: Optional["PerfilCliente"] = Relationship(
        back_populates="cliente",
        sa_relationship_kwargs={"uselist": False},
    )
    ventas: list["Venta"] = Relationship(back_populates="cliente")


class PerfilCliente(SQLModel, table=True):
    """Perfil de contacto de un cliente.

    La restricción `UNIQUE` sobre `cliente_id` es la que sostiene la relación
    uno a uno en la base y la que rechaza un segundo perfil para el mismo
    cliente.
    """

    __tablename__ = "perfil_cliente"

    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id", unique=True)
    telefono: Optional[str] = Field(default=None)
    direccion: Optional[str] = Field(default=None)

    cliente: Optional["Cliente"] = Relationship(back_populates="perfil")
