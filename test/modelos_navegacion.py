"""Recorre las relaciones del dominio en los dos sentidos sobre la semilla.

El script es de solo lectura: abre una sesión con la configuración del
proyecto, carga cada relación de forma explícita y afirma la cardinalidad de
los dos extremos. Requiere la base sembrada por `scripts/datos_iniciales.py`.

Uso:
    .venv\\Scripts\\python.exe test\\modelos_navegacion.py

Imprime `ok` y termina con código 0 si todas las comprobaciones pasan.
"""

import asyncio
import sys
from pathlib import Path

# Permite ejecutar el archivo directamente sin depender de PYTHONPATH.
_RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.orm import selectinload  # noqa: E402
from sqlmodel import select  # noqa: E402
from sqlmodel.ext.asyncio.session import AsyncSession  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.registry import import_model_modules  # noqa: E402
from app.modules.autores.models import Autor  # noqa: E402
from app.modules.clientes.models import Cliente, PerfilCliente  # noqa: E402
from app.modules.editoriales.models import Editorial  # noqa: E402
from app.modules.generos.models import Genero  # noqa: E402
from app.modules.libros.models import Libro, LibroAutor  # noqa: E402
from app.modules.ventas.models import RenglonVenta, Venta  # noqa: E402


async def _verificar_cliente_perfil(session: AsyncSession) -> None:
    """Comprueba que el perfil se navega como objeto en los dos sentidos."""
    cliente = (
        await session.exec(
            select(Cliente)
            .options(
                selectinload(Cliente.perfil).selectinload(PerfilCliente.cliente)
            )
            .order_by(Cliente.id)
            .limit(1)
        )
    ).one()

    assert cliente.perfil is not None, "El cliente sembrado no tiene perfil."
    assert not isinstance(cliente.perfil, list), (
        "Cliente.perfil debe ser un objeto, no una colección."
    )
    assert isinstance(cliente.perfil, PerfilCliente), (
        "Cliente.perfil debe ser una instancia de PerfilCliente."
    )
    assert cliente.perfil.cliente is not None, "El perfil no referencia a su cliente."
    assert cliente.perfil.cliente.id == cliente.id, (
        "PerfilCliente.cliente no vuelve al cliente de origen."
    )


async def _verificar_libro_genero(session: AsyncSession) -> None:
    """Comprueba la agregación opcional libro-género en ambos sentidos."""
    libro_sin_genero = (
        await session.exec(
            select(Libro)
            .options(selectinload(Libro.genero))
            .where(Libro.genero_id.is_(None))
        )
    ).one()
    assert libro_sin_genero.genero is None, (
        "Un libro con genero_id nulo debe exponer género nulo."
    )

    libro_con_genero = (
        await session.exec(
            select(Libro)
            .options(selectinload(Libro.genero))
            .where(Libro.genero_id.is_not(None))
            .order_by(Libro.id)
            .limit(1)
        )
    ).one()
    assert libro_con_genero.genero is not None, "El libro debería tener género."
    assert libro_con_genero.genero.id == libro_con_genero.genero_id, (
        "Libro.genero no coincide con genero_id."
    )

    genero = (
        await session.exec(
            select(Genero)
            .options(selectinload(Genero.libros))
            .where(Genero.id == libro_con_genero.genero_id)
        )
    ).one()
    assert genero.libros, "El género debería agrupar libros."
    assert all(libro.genero_id == genero.id for libro in genero.libros), (
        "Algún libro de Genero.libros no referencia al mismo género."
    )


async def _verificar_libro_autorias(session: AsyncSession) -> None:
    """Comprueba la navegación libro -> autoría -> autor y autor -> libro."""
    libro = (
        await session.exec(
            select(Libro)
            .options(selectinload(Libro.autorias).selectinload(LibroAutor.autor))
            .where(Libro.titulo == "Freakonomics")
        )
    ).one()

    assert len(libro.autorias) == 2, "Freakonomics debería tener dos autorías."
    assert {(a.rol, a.orden) for a in libro.autorias} == {
        ("autor", 1),
        ("coautor", 2),
    }, "Los roles y el orden de Freakonomics no coinciden con la semilla."

    for autoria in libro.autorias:
        assert autoria.libro_id == libro.id, "La autoría no apunta a su libro."
        assert autoria.autor is not None, "La autoría no expone su autor."
        assert autoria.autor.id == autoria.autor_id, (
            "LibroAutor.autor no coincide con autor_id."
        )

    autor = (
        await session.exec(
            select(Autor)
            .options(selectinload(Autor.autorias).selectinload(LibroAutor.libro))
            .where(Autor.id == libro.autorias[0].autor_id)
        )
    ).one()
    assert autor.autorias, "El autor debería tener autorías."
    assert any(
        autoria.libro is not None and autoria.libro.id == libro.id
        for autoria in autor.autorias
    ), "Autor.autorias no vuelve al libro de origen."


async def _verificar_venta_renglones(session: AsyncSession) -> None:
    """Comprueba la composición venta-renglón y las asociaciones con cliente y libro."""
    venta = (
        await session.exec(
            select(Venta)
            .options(
                selectinload(Venta.renglones).selectinload(RenglonVenta.libro),
                selectinload(Venta.cliente),
            )
            .order_by(Venta.id)
            .limit(1)
        )
    ).one()

    assert venta.renglones, "La venta sembrada debería tener renglones."
    assert venta.cliente is not None, "La venta no expone su cliente."
    assert venta.cliente.id == venta.cliente_id, (
        "Venta.cliente no coincide con cliente_id."
    )

    for renglon in venta.renglones:
        assert renglon.venta_id == venta.id, "El renglón no apunta a su venta."
        assert renglon.libro is not None, "El renglón no expone su libro."
        assert renglon.libro.id == renglon.libro_id, (
            "RenglonVenta.libro no coincide con libro_id."
        )

    libro = (
        await session.exec(
            select(Libro)
            .options(selectinload(Libro.renglones))
            .where(Libro.id == venta.renglones[0].libro_id)
        )
    ).one()
    assert libro.renglones, "El libro debería aparecer en renglones."
    assert any(
        renglon.id == venta.renglones[0].id for renglon in libro.renglones
    ), "Libro.renglones no incluye el renglón de la venta."
    assert all(renglon.libro_id == libro.id for renglon in libro.renglones), (
        "Algún renglón de Libro.renglones no referencia al mismo libro."
    )

    cliente = (
        await session.exec(
            select(Cliente)
            .options(selectinload(Cliente.ventas))
            .where(Cliente.id == venta.cliente_id)
        )
    ).one()
    assert any(v.id == venta.id for v in cliente.ventas), (
        "Cliente.ventas no incluye la venta de origen."
    )
    assert all(v.cliente_id == cliente.id for v in cliente.ventas), (
        "Alguna venta de Cliente.ventas no referencia al mismo cliente."
    )


async def _verificar_editorial_libros(session: AsyncSession) -> None:
    """Comprueba la colección inversa de libros desde la editorial."""
    editorial = (
        await session.exec(
            select(Editorial)
            .options(selectinload(Editorial.libros))
            .order_by(Editorial.id)
            .limit(1)
        )
    ).one()
    assert editorial.libros, "La editorial debería publicar libros."
    assert all(libro.editorial_id == editorial.id for libro in editorial.libros), (
        "Algún libro de Editorial.libros no referencia a la misma editorial."
    )


async def main() -> None:
    """Abre una sesión y ejecuta todas las comprobaciones de navegación."""
    import_model_modules()
    settings = get_settings()

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    try:
        async with session_factory() as session:
            await _verificar_cliente_perfil(session)
            await _verificar_libro_genero(session)
            await _verificar_libro_autorias(session)
            await _verificar_venta_renglones(session)
            await _verificar_editorial_libros(session)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
    print("ok")
