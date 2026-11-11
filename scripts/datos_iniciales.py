"""Carga la semilla del frontend en la base configurada por `DATABASE_URL`.

La fuente es `libreria_abc/js/datos-iniciales.js`. El script traduce los ids de
texto a claves enteras generadas por PostgreSQL, conserva los importes como
`Decimal`, crea una autoría por cada relación libro-autor y un perfil por
cliente, y recalcula el total de cada venta antes de confirmar la transacción.

Uso:
    .venv\\Scripts\\python.exe scripts\\datos_iniciales.py

Si la base ya tiene filas en alguna de las nueve tablas del dominio, el script
no escribe nada e informa la situación con código de salida 0. Cualquier error
de conexión o de datos termina con código distinto de cero y sin confirmar
filas, porque toda la carga ocurre en una única transacción.
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

# Permite ejecutar el archivo directamente sin depender de PYTHONPATH.
_RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.registry import import_model_modules  # noqa: E402
from app.modules.autores.models import Autor  # noqa: E402
from app.modules.clientes.models import Cliente, PerfilCliente  # noqa: E402
from app.modules.editoriales.models import Editorial  # noqa: E402
from app.modules.generos.models import Genero  # noqa: E402
from app.modules.libros.models import Libro, LibroAutor  # noqa: E402
from app.modules.ventas.models import RenglonVenta, Venta  # noqa: E402

# Desplazamiento horario del negocio: las fechas de la semilla no traen hora y
# se interpretan como las 00:00 de Argentina (UTC-3).
_ZONA_HORARIA = timezone(timedelta(hours=-3))

# Stock asignado a cada libro: la semilla del frontend no registra existencias,
# así que se usa un valor explícito y documentado en lugar de un default del
# modelo. Si aparecen datos reales, se cambian acá sin tocar el esquema.
_STOCK_INICIAL = 10

_EDITORIALES: tuple[str, ...] = (
    "Editorial Sudamericana",
    "Editorial Planeta",
    "Salamandra",
    "Lumen",
    "Seix Barral",
    "Crítica",
    "Alfaguara",
)

_GENEROS: tuple[str, ...] = (
    "Realismo Mágico",
    "Fantasía",
    "Misterio",
    "Novela",
    "Ensayo",
)

_AUTORES: tuple[str, ...] = (
    "Gabriel García Márquez",
    "J. R. R. Tolkien",
    "J. K. Rowling",
    "Umberto Eco",
    "Julio Cortázar",
    "Yuval Noah Harari",
    "Miguel de Cervantes",
    "Pablo Neruda",
    "Steven Levitt",
    "Stephen Dubner",
)

# Cada libro conserva el ISBN y el precio de la semilla. `genero` en `None`
# reproduce el `generoId: null` de "Veinte poemas de amor".
_LIBROS: tuple[dict[str, Any], ...] = (
    {
        "titulo": "Cien años de soledad",
        "isbn": "9780307474728",
        "editorial": "Editorial Sudamericana",
        "genero": "Realismo Mágico",
        "autores": ("Gabriel García Márquez",),
        "precio": "24500.00",
    },
    {
        "titulo": "El Hobbit",
        "isbn": "9789507324786",
        "editorial": "Editorial Planeta",
        "genero": "Fantasía",
        "autores": ("J. R. R. Tolkien",),
        "precio": "21900.00",
    },
    {
        "titulo": "Harry Potter y la piedra filosofal",
        "isbn": "9788498922228",
        "editorial": "Salamandra",
        "genero": "Fantasía",
        "autores": ("J. K. Rowling",),
        "precio": "28500.00",
    },
    {
        "titulo": "El nombre de la rosa",
        "isbn": "9788499890524",
        "editorial": "Lumen",
        "genero": "Misterio",
        "autores": ("Umberto Eco",),
        "precio": "19900.00",
    },
    {
        "titulo": "Rayuela",
        "isbn": "9788437604576",
        "editorial": "Seix Barral",
        "genero": "Novela",
        "autores": ("Julio Cortázar",),
        "precio": "17900.00",
    },
    {
        "titulo": "Sapiens: De animales a dioses",
        "isbn": "9788499926223",
        "editorial": "Crítica",
        "genero": "Ensayo",
        "autores": ("Yuval Noah Harari",),
        "precio": "32900.00",
    },
    {
        "titulo": "Don Quijote de la Mancha",
        "isbn": "9788467034451",
        "editorial": "Editorial Planeta",
        "genero": "Novela",
        "autores": ("Miguel de Cervantes",),
        "precio": "15900.00",
    },
    {
        "titulo": "Veinte poemas de amor",
        "isbn": "9788478886680",
        "editorial": "Alfaguara",
        "genero": None,
        "autores": ("Pablo Neruda",),
        "precio": "13900.00",
    },
    {
        "titulo": "Freakonomics",
        "isbn": "9788499922223",
        "editorial": "Crítica",
        "genero": "Ensayo",
        "autores": ("Steven Levitt", "Stephen Dubner"),
        "precio": "25900.00",
    },
)

_CLIENTES: tuple[tuple[str, str], ...] = (
    ("Martina Ferreyra", "martina.ferreyra@example.com"),
    ("Diego Sosa", "diego.sosa@example.com"),
    ("Lucía Bianchi", "lucia.bianchi@example.com"),
    ("Nicolás Ferreyra", "nicolas.ferreyra@example.com"),
)

# Los renglones identifican el libro por ISBN (clave natural de la semilla).
# El total esperado se contrasta con el que resulta de cantidad por precio.
_VENTAS: tuple[dict[str, Any], ...] = (
    {
        "fecha": datetime(2026, 3, 14, 0, 0, tzinfo=_ZONA_HORARIA),
        "cliente": "martina.ferreyra@example.com",
        "renglones": (
            ("9788467034451", 2),  # Don Quijote de la Mancha
            ("9789507324786", 1),  # El Hobbit
        ),
        "total": "53700.00",
    },
    {
        "fecha": datetime(2026, 4, 2, 0, 0, tzinfo=_ZONA_HORARIA),
        "cliente": "diego.sosa@example.com",
        "renglones": (
            ("9788499926223", 1),  # Sapiens: De animales a dioses
            ("9788498922228", 2),  # Harry Potter y la piedra filosofal
        ),
        "total": "89900.00",
    },
)

_MODELOS_DOMINIO: tuple[type[SQLModel], ...] = (
    Editorial,
    Genero,
    Autor,
    Libro,
    LibroAutor,
    Cliente,
    PerfilCliente,
    Venta,
    RenglonVenta,
)


async def _contar_filas(session: AsyncSession, modelo: type[SQLModel]) -> int:
    """Devuelve la cantidad de filas de una tabla del dominio."""
    resultado = await session.execute(select(func.count()).select_from(modelo))
    return resultado.scalar_one()


async def _conteos_por_tabla(session: AsyncSession) -> dict[str, int]:
    """Cuenta las filas de las nueve tablas, en el orden del modelo."""
    conteos: dict[str, int] = {}
    for modelo in _MODELOS_DOMINIO:
        conteos[modelo.__tablename__] = await _contar_filas(session, modelo)
    return conteos


def _avisar_base_poblada(conteos: dict[str, int]) -> None:
    """Informa que la base ya tiene datos y que no se escribió nada."""
    print("ADVERTENCIA: la base ya contiene datos de dominio.")
    print("No se cargó ninguna fila para no duplicar información.")
    for tabla, cantidad in conteos.items():
        if cantidad:
            print(f"  {tabla}: {cantidad} fila(s)")
    print("Para volver a sembrar, recreá el esquema y ejecutá el script de nuevo.")


async def _sembrar(session: AsyncSession) -> dict[str, int]:
    """Inserta la semilla completa dentro de la transacción de la sesión."""
    editoriales: dict[str, Editorial] = {}
    for nombre in _EDITORIALES:
        # El frontend no registra países: se dejan en NULL.
        editorial = Editorial(nombre=nombre, pais=None)
        session.add(editorial)
        editoriales[nombre] = editorial

    generos: dict[str, Genero] = {}
    for nombre in _GENEROS:
        genero = Genero(nombre=nombre)
        session.add(genero)
        generos[nombre] = genero

    autores: dict[str, Autor] = {}
    for nombre in _AUTORES:
        # El frontend no registra nacionalidades: se dejan en NULL.
        autor = Autor(nombre=nombre, nacionalidad=None)
        session.add(autor)
        autores[nombre] = autor

    await session.flush()

    libros: dict[str, Libro] = {}
    for datos in _LIBROS:
        libro = Libro(
            isbn=datos["isbn"],
            titulo=datos["titulo"],
            precio=Decimal(datos["precio"]),
            stock=_STOCK_INICIAL,
            editorial_id=editoriales[datos["editorial"]].id,
            genero_id=generos[datos["genero"]].id if datos["genero"] else None,
        )
        session.add(libro)
        libros[libro.isbn] = libro

    await session.flush()

    for datos in _LIBROS:
        libro = libros[datos["isbn"]]
        for posicion, nombre_autor in enumerate(datos["autores"], start=1):
            session.add(
                LibroAutor(
                    libro_id=libro.id,
                    autor_id=autores[nombre_autor].id,
                    rol="autor" if posicion == 1 else "coautor",
                    orden=posicion,
                )
            )

    clientes: dict[str, Cliente] = {}
    for nombre, email in _CLIENTES:
        cliente = Cliente(nombre=nombre, email=email)
        session.add(cliente)
        clientes[email] = cliente

    await session.flush()

    for cliente in clientes.values():
        # Un perfil por cliente; la semilla no trae teléfono ni dirección.
        session.add(
            PerfilCliente(cliente_id=cliente.id, telefono=None, direccion=None)
        )

    await session.flush()

    for datos in _VENTAS:
        total = Decimal("0.00")
        renglones: list[tuple[Libro, int, Decimal]] = []
        for isbn, cantidad in datos["renglones"]:
            libro = libros[isbn]
            precio_unitario = libro.precio
            renglones.append((libro, cantidad, precio_unitario))
            total += precio_unitario * cantidad

        esperado = Decimal(datos["total"])
        if total != esperado:
            raise RuntimeError(
                "El total recalculado no coincide con la semilla: "
                f"esperado {esperado}, calculado {total}."
            )

        venta = Venta(
            cliente_id=clientes[datos["cliente"]].id,
            fecha=datos["fecha"],
            total=total,
        )
        session.add(venta)
        await session.flush()

        for libro, cantidad, precio_unitario in renglones:
            session.add(
                RenglonVenta(
                    venta_id=venta.id,
                    libro_id=libro.id,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                )
            )

    await session.flush()
    return await _conteos_por_tabla(session)


async def main() -> int:
    """Crea el esquema si falta, verifica la base vacía y carga la semilla."""
    import_model_modules()
    settings = get_settings()

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with session_factory() as session:
            conteos_previos = await _conteos_por_tabla(session)
            if any(conteos_previos.values()):
                _avisar_base_poblada(conteos_previos)
                return 0

            try:
                conteos = await _sembrar(session)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        print("Datos iniciales cargados en una sola transacción:")
        for tabla, cantidad in conteos.items():
            print(f"  {tabla}: {cantidad}")
        return 0
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        codigo_salida = asyncio.run(main())
    except Exception as error:  # noqa: BLE001
        print(
            f"Error al cargar los datos iniciales: {error}",
            file=sys.stderr,
        )
        print(
            "No se confirmó ningún dato. Revisá DATABASE_URL y que la base "
            "esté disponible.",
            file=sys.stderr,
        )
        sys.exit(1)
    sys.exit(codigo_salida)
