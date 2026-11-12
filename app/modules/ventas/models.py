"""Modelos de tabla de ventas y de sus renglones.

El módulo se importa desde `app.core.registry.import_model_modules()` antes de
`create_all`; cualquier script que use estas clases debe llamar primero a esa
función para que SQLAlchemy configure todos los mapeos del dominio.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.libros.models import Libro


class Venta(SQLModel, table=True):
    """Venta de libros a un cliente, compuesta por renglones.

    La fecha se guarda como instante con zona horaria y el total como
    `Numeric(12, 2)`, que admite el acumulado de varios renglones.
    """

    __tablename__ = "venta"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_venta_total_no_negativo"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id", index=True)
    fecha: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    total: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))

    cliente: Optional["Cliente"] = Relationship(
        back_populates="ventas", sa_relationship_kwargs={"lazy": "raise"}
    )
    # La cascada de la base elimina los renglones con `ON DELETE CASCADE`;
    # `passive_deletes` evita que SQLAlchemy los cargue solo para borrarlos.
    renglones: list["RenglonVenta"] = Relationship(
        back_populates="venta",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
            "lazy": "raise",
        },
    )


class RenglonVenta(SQLModel, table=True):
    """Renglón de una venta con el precio unitario histórico del libro.

    `precio_unitario` se copia del libro al momento de la venta y no se
    recalcula después, de modo que el historial no cambia si el catálogo
    actualiza su precio.
    """

    __tablename__ = "renglon_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_renglon_venta_cantidad_positiva"),
        CheckConstraint(
            "precio_unitario > 0",
            name="ck_renglon_venta_precio_positivo",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    venta_id: int = Field(foreign_key="venta.id", ondelete="CASCADE", index=True)
    libro_id: int = Field(foreign_key="libro.id", index=True)
    cantidad: int
    precio_unitario: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False)
    )

    venta: Optional["Venta"] = Relationship(
        back_populates="renglones", sa_relationship_kwargs={"lazy": "raise"}
    )
    libro: Optional["Libro"] = Relationship(
        back_populates="renglones", sa_relationship_kwargs={"lazy": "raise"}
    )
