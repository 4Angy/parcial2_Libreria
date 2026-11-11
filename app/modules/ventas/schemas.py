"""DTO de ventas y de sus renglones.

La fecha se publica en ISO 8601 UTC terminada en `Z` y los importes como
cadenas decimales. `RenglonRead` aplana el título del libro y calcula el
subtotal a partir de la entidad ORM.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from app.modules.clientes.schemas import ClienteRef

_CENTAVOS = Decimal("0.01")


def _calcular_subtotal(precio_unitario: Decimal, cantidad: int) -> Decimal:
    """Multiplica el precio histórico por la cantidad con dos decimales."""
    return (Decimal(precio_unitario) * Decimal(cantidad)).quantize(_CENTAVOS)


def _titulo_del_libro(libro: Any) -> Optional[str]:
    """Obtiene el título de un libro ORM o de un diccionario."""
    if libro is None:
        return None
    if isinstance(libro, dict):
        return libro.get("titulo")
    return getattr(libro, "titulo", None)


class RenglonRead(BaseModel):
    """Renglón de una venta con el título del libro y su subtotal."""

    model_config = ConfigDict(from_attributes=True)

    libro_id: int
    titulo: Optional[str] = None
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal

    @model_validator(mode="before")
    @classmethod
    def _aplanar_libro_y_subtotal(cls, datos: Any) -> Any:
        """Deriva `titulo` y `subtotal` cuando la entrada es una entidad ORM.

        Si la entrada ya trae los campos del contrato (por ejemplo un
        diccionario de prueba), se deja pasar sin cambios.
        """
        if isinstance(datos, dict):
            if "subtotal" in datos:
                return datos
            libro = datos.get("libro")
            precio = datos.get("precio_unitario")
            cantidad = datos.get("cantidad")
            if precio is None or cantidad is None:
                return datos
            return {
                "libro_id": datos.get("libro_id"),
                "titulo": _titulo_del_libro(libro),
                "cantidad": cantidad,
                "precio_unitario": precio,
                "subtotal": _calcular_subtotal(precio, cantidad),
            }

        precio = getattr(datos, "precio_unitario", None)
        cantidad = getattr(datos, "cantidad", None)
        if precio is None or cantidad is None:
            return datos
        return {
            "libro_id": getattr(datos, "libro_id", None),
            "titulo": _titulo_del_libro(getattr(datos, "libro", None)),
            "cantidad": cantidad,
            "precio_unitario": precio,
            "subtotal": _calcular_subtotal(precio, cantidad),
        }


class VentaResumenRead(BaseModel):
    """Venta de un listado: sin cliente ni renglones."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime
    total: Decimal

    @field_serializer("fecha")
    def _serializar_fecha(self, fecha: datetime) -> str:
        """Normaliza a UTC y reemplaza el desplazamiento por `Z`."""
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        return fecha.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class VentaRead(VentaResumenRead):
    """Detalle de una venta con su cliente y sus renglones."""

    cliente: Optional[ClienteRef] = None
    renglones: list[RenglonRead] = Field(default_factory=list)
