"""Comprueba la forma serializada de los DTO sin tocar la base.

Construye entidades ORM en memoria y valida que los contratos de lectura
serialicen importes como cadena, fechas en UTC terminadas en `Z`, enteros como
números y relaciones aplanadas como las publica la API.

Uso:
    .venv\\Scripts\\python.exe test\\serializacion.py

Imprime `ok` y termina con código 0 si todas las comprobaciones pasan.
"""

import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable

# Permite ejecutar el archivo directamente sin depender de PYTHONPATH.
_RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

from pydantic import ValidationError  # noqa: E402

from app.modules.autores.models import Autor  # noqa: E402
from app.modules.autores.schemas import (  # noqa: E402
    AutorCreate,
    AutorRead,
    AutorUpdate,
)
from app.modules.clientes.models import Cliente, PerfilCliente  # noqa: E402
from app.modules.clientes.schemas import (  # noqa: E402
    ClienteRead,
    ClienteUpdate,
    PerfilCreate,
)
from app.modules.editoriales.models import Editorial  # noqa: E402
from app.modules.editoriales.schemas import (  # noqa: E402
    EditorialCreate,
    EditorialRead,
    EditorialUpdate,
)
from app.modules.generos.models import Genero  # noqa: E402
from app.modules.generos.schemas import GeneroCreate, GeneroRead  # noqa: E402
from app.modules.libros.models import Libro, LibroAutor  # noqa: E402
from app.modules.libros.schemas import (  # noqa: E402
    LibroAutorCreate,
    LibroCreate,
    LibroDeAutorRead,
    LibroRead,
    LibroResumenRead,
    LibroUpdate,
)
from app.modules.ventas.models import RenglonVenta, Venta  # noqa: E402
from app.modules.ventas.schemas import (  # noqa: E402
    RenglonCreate,
    RenglonRead,
    VentaCreate,
    VentaRead,
    VentaResumenRead,
)


def _rechaza(funcion: Callable[[], object], caso: str) -> None:
    """Afirma que la construcción del DTO lanza `ValidationError`."""
    try:
        funcion()
    except ValidationError:
        return
    raise AssertionError(f"{caso} debía fallar la validación.")


def _editoriales() -> None:
    """Altas sin `id`, actualización parcial y lectura desde ORM."""
    assert EditorialCreate(nombre="Nueva").nombre == "Nueva"
    _rechaza(
        lambda: EditorialCreate(id=99, nombre="Nueva"),
        "EditorialCreate con id",
    )
    _rechaza(
        lambda: EditorialCreate(nombre="Nueva", desconocido=1),
        "EditorialCreate con campo desconocido",
    )

    assert EditorialUpdate(nombre="X").model_dump(exclude_unset=True) == {
        "nombre": "X"
    }
    assert EditorialUpdate().model_dump(exclude_unset=True) == {}

    editorial = Editorial(id=1, nombre="Salamandra", pais="Argentina")
    datos = EditorialRead.model_validate(editorial).model_dump(mode="json")
    assert datos == {"id": 1, "nombre": "Salamandra", "pais": "Argentina"}


def _generos() -> None:
    """Alta sin `id` y lectura desde ORM."""
    assert GeneroCreate(nombre="Nuevo").nombre == "Nuevo"
    _rechaza(
        lambda: GeneroCreate(nombre="Nuevo", id=1),
        "GeneroCreate con id",
    )
    genero = Genero(id=2, nombre="Fantasía")
    assert GeneroRead.model_validate(genero).model_dump(mode="json") == {
        "id": 2,
        "nombre": "Fantasía",
    }


def _autores() -> None:
    """Alta obligatoria, actualización parcial y lectura desde ORM."""
    assert AutorCreate(nombre="Nuevo", nacionalidad="Chile").nombre == "Nuevo"
    _rechaza(
        lambda: AutorCreate(nacionalidad="Chile"),
        "AutorCreate sin nombre",
    )
    assert AutorUpdate(nacionalidad="Chile").model_dump(exclude_unset=True) == {
        "nacionalidad": "Chile"
    }
    autor = Autor(id=3, nombre="Umberto Eco", nacionalidad=None)
    assert AutorRead.model_validate(autor).model_dump(mode="json") == {
        "id": 3,
        "nombre": "Umberto Eco",
        "nacionalidad": None,
    }


def _libro_de_prueba() -> Libro:
    """Arma un libro ORM con editorial, género y una autoría."""
    editorial = Editorial(id=1, nombre="Editorial Sudamericana", pais=None)
    genero = Genero(id=1, nombre="Realismo Mágico")
    autor = Autor(id=1, nombre="Gabriel García Márquez", nacionalidad=None)
    autoria = LibroAutor(libro_id=1, autor_id=1, rol="autor", orden=1)
    autoria.autor = autor

    libro = Libro(
        id=1,
        isbn="9780307474728",
        titulo="Cien años de soledad",
        precio=Decimal("24500.00"),
        stock=10,
        editorial_id=1,
        genero_id=1,
    )
    libro.editorial = editorial
    libro.genero = genero
    libro.autorias = [autoria]
    return libro


def _libros() -> None:
    """Rangos del `PATCH`, importes como cadena y relaciones aplanadas."""
    _rechaza(lambda: LibroUpdate(precio=0), "LibroUpdate con precio 0")
    _rechaza(lambda: LibroUpdate(stock=-1), "LibroUpdate con stock negativo")
    assert LibroUpdate().model_dump(exclude_unset=True) == {}
    assert LibroUpdate(genero_id=None).model_dump(exclude_unset=True) == {
        "genero_id": None
    }

    libro = _libro_de_prueba()
    datos = LibroRead.model_validate(libro).model_dump(mode="json")
    assert datos["precio"] == "24500.00", datos["precio"]
    assert datos["stock"] == 10 and isinstance(datos["stock"], int)
    assert datos["editorial"] == {"id": 1, "nombre": "Editorial Sudamericana"}
    assert datos["genero"] == {"id": 1, "nombre": "Realismo Mágico"}
    assert datos["autores"] == [
        {
            "autor": {"id": 1, "nombre": "Gabriel García Márquez"},
            "rol": "autor",
            "orden": 1,
        }
    ]

    resumen = LibroResumenRead.model_validate(libro).model_dump(mode="json")
    assert "autores" not in resumen

    libro.genero = None
    libro.genero_id = None
    sin_genero = LibroRead.model_validate(libro).model_dump(mode="json")
    assert sin_genero["genero"] is None, sin_genero["genero"]

    autoria = libro.autorias[0]
    autoria.libro = libro
    de_autor = LibroDeAutorRead.model_validate(autoria).model_dump(mode="json")
    assert de_autor["rol"] == "autor" and de_autor["orden"] == 1
    assert de_autor["libro"]["id"] == 1


def _clientes() -> None:
    """Perfil sin `cliente_id` y lectura como objeto o `null`, nunca lista."""
    _rechaza(
        lambda: PerfilCreate(cliente_id=1, telefono="123"),
        "PerfilCreate con cliente_id",
    )
    assert PerfilCreate(telefono="123", direccion="Calle 1").telefono == "123"

    assert ClienteUpdate(nombre="X").model_dump(exclude_unset=True) == {
        "nombre": "X"
    }

    perfil = PerfilCliente(id=1, cliente_id=1, telefono=None, direccion=None)
    con_perfil = Cliente(
        id=1,
        nombre="Martina Ferreyra",
        email="martina.ferreyra@example.com",
        perfil=perfil,
    )
    datos = ClienteRead.model_validate(con_perfil).model_dump(mode="json")
    assert datos["perfil"] == {
        "id": 1,
        "telefono": None,
        "direccion": None,
    }, datos["perfil"]
    assert not isinstance(datos["perfil"], list)

    sin_perfil = Cliente(
        id=2,
        nombre="Cliente Nuevo",
        email="nuevo@example.com",
        perfil=None,
    )
    datos = ClienteRead.model_validate(sin_perfil).model_dump(mode="json")
    assert datos["perfil"] is None, datos["perfil"]


def _ventas() -> None:
    """Fecha UTC con `Z`, importes como cadena y renglón aplanado."""
    cliente = Cliente(
        id=1,
        nombre="Martina Ferreyra",
        email="martina.ferreyra@example.com",
        perfil=None,
    )
    libro = Libro(
        id=7,
        isbn="9788467034451",
        titulo="Don Quijote de la Mancha",
        precio=Decimal("15900.00"),
        stock=10,
        editorial_id=2,
        genero_id=4,
    )
    renglon = RenglonVenta(
        id=1,
        venta_id=1,
        libro_id=7,
        cantidad=2,
        precio_unitario=Decimal("15900.00"),
    )
    renglon.libro = libro

    fecha = datetime(2026, 10, 8, 21, 14, 11, 751581, tzinfo=timezone.utc)
    venta = Venta(
        id=1,
        cliente_id=1,
        fecha=fecha,
        total=Decimal("53700.00"),
    )
    venta.cliente = cliente
    venta.renglones = [renglon]

    datos = VentaRead.model_validate(venta).model_dump(mode="json")
    assert datos["fecha"] == "2026-10-08T21:14:11.751581Z", datos["fecha"]
    assert datos["total"] == "53700.00", datos["total"]
    assert datos["cliente"]["id"] == 1
    assert datos["renglones"][0] == {
        "libro_id": 7,
        "titulo": "Don Quijote de la Mancha",
        "cantidad": 2,
        "precio_unitario": "15900.00",
        "subtotal": "31800.00",
    }, datos["renglones"][0]

    resumen = VentaResumenRead.model_validate(venta).model_dump(mode="json")
    assert set(resumen) == {"id", "fecha", "total"}
    assert resumen["fecha"] == "2026-10-08T21:14:11.751581Z"

    directo = RenglonRead.model_validate(
        {
            "libro_id": 2,
            "titulo": "El Hobbit",
            "cantidad": 1,
            "precio_unitario": Decimal("21900.00"),
            "subtotal": Decimal("21900.00"),
        }
    )
    assert directo.subtotal == Decimal("21900.00")


def _altas_con_relaciones() -> None:
    """Matriz de los DTO de alta de libro y de venta, sin tocar la base."""
    libro = LibroCreate(
        isbn="978-950-00-0006-6",
        titulo="Los que aman, odian",
        precio="21000.00",
        stock=4,
        editorial_id=1,
        genero_id=1,
        autores=[
            {"autor_id": 3, "rol": "coautor", "orden": 1},
            {"autor_id": 4, "rol": "coautor", "orden": 2},
        ],
    )
    assert libro.precio == Decimal("21000.00")
    assert isinstance(libro.precio, Decimal)
    assert [autoria.autor_id for autoria in libro.autores] == [3, 4]
    assert libro.autores[1].orden == 2

    sin_autores = LibroCreate(
        isbn="978-950-00-0007-3",
        titulo="Prueba 04 Sin Autores",
        precio="1000.00",
        stock=0,
        editorial_id=1,
        autores=[],
    )
    assert sin_autores.autores == []
    assert sin_autores.genero_id is None

    assert LibroAutorCreate(
        autor_id=1, rol="traductor", orden=1
    ).rol == "traductor"

    _rechaza(
        lambda: LibroCreate(
            id=99,
            isbn="978-950-00-0008-0",
            titulo="Prueba 04 Con Id",
            precio="1000.00",
            stock=1,
            editorial_id=1,
            autores=[],
        ),
        "LibroCreate con id",
    )
    _rechaza(
        lambda: LibroCreate(
            isbn="978-950-00-0009-7",
            titulo="Prueba 04 Con Campo",
            precio="1000.00",
            stock=1,
            editorial_id=1,
            autores=[],
            desconocido=True,
        ),
        "LibroCreate con campo desconocido",
    )
    _rechaza(
        lambda: LibroAutorCreate(autor_id=1, rol="autor", orden=1, extra=1),
        "LibroAutorCreate con campo desconocido",
    )
    _rechaza(
        lambda: LibroCreate(
            isbn="978-950-00-0010-3",
            titulo="Prueba 04 Precio",
            precio="0",
            stock=1,
            editorial_id=1,
            autores=[],
        ),
        "LibroCreate con precio 0",
    )
    _rechaza(
        lambda: LibroCreate(
            isbn="978-950-00-0011-0",
            titulo="Prueba 04 Stock",
            precio="1000.00",
            stock=-1,
            editorial_id=1,
            autores=[],
        ),
        "LibroCreate con stock negativo",
    )
    _rechaza(
        lambda: LibroAutorCreate(autor_id=1, rol="prologuista", orden=1),
        "LibroAutorCreate con rol inválido",
    )
    _rechaza(
        lambda: LibroAutorCreate(autor_id=1, rol="autor", orden=0),
        "LibroAutorCreate con orden 0",
    )
    _rechaza(
        lambda: LibroCreate(
            isbn="978-950-00-0012-7",
            titulo="Prueba 04 Autor Repetido",
            precio="1000.00",
            stock=1,
            editorial_id=1,
            autores=[
                {"autor_id": 1, "rol": "autor", "orden": 1},
                {"autor_id": 1, "rol": "coautor", "orden": 2},
            ],
        ),
        "LibroCreate con autor repetido",
    )
    _rechaza(
        lambda: LibroCreate(
            isbn="978-950-00-0013-4",
            titulo="Prueba 04 Orden Repetido",
            precio="1000.00",
            stock=1,
            editorial_id=1,
            autores=[
                {"autor_id": 1, "rol": "autor", "orden": 1},
                {"autor_id": 2, "rol": "coautor", "orden": 1},
            ],
        ),
        "LibroCreate con orden repetido",
    )
    _rechaza(
        lambda: LibroCreate(
            isbn="978-950-00-0014-1",
            titulo="Prueba 04 Sin Autores Declarados",
            precio="1000.00",
            stock=1,
            editorial_id=1,
        ),
        "LibroCreate sin la clave autores",
    )

    venta = VentaCreate(
        cliente_id=2,
        renglones=[
            {"libro_id": 1, "cantidad": 2},
            {"libro_id": 4, "cantidad": 1},
        ],
    )
    assert [renglon.libro_id for renglon in venta.renglones] == [1, 4]
    assert RenglonCreate(libro_id=1, cantidad=1).cantidad == 1

    _rechaza(
        lambda: VentaCreate(cliente_id=2, renglones=[]),
        "VentaCreate sin renglones",
    )
    _rechaza(
        lambda: RenglonCreate(libro_id=1, cantidad=0),
        "RenglonCreate con cantidad 0",
    )
    _rechaza(
        lambda: VentaCreate(
            cliente_id=2,
            renglones=[
                {"libro_id": 1, "cantidad": 1},
                {"libro_id": 1, "cantidad": 2},
            ],
        ),
        "VentaCreate con libro repetido",
    )
    _rechaza(
        lambda: VentaCreate(
            cliente_id=2,
            renglones=[{"libro_id": 1, "cantidad": 1}],
            desconocido=True,
        ),
        "VentaCreate con campo desconocido",
    )
    _rechaza(
        lambda: RenglonCreate(libro_id=1, cantidad=1, extra=1),
        "RenglonCreate con campo desconocido",
    )
    _rechaza(
        lambda: VentaCreate(
            cliente_id=2,
            renglones=[{"libro_id": 1, "cantidad": 1}],
            total="68900.00",
        ),
        "VentaCreate con total",
    )
    _rechaza(
        lambda: RenglonCreate(
            libro_id=1, cantidad=1, precio_unitario="24500.00"
        ),
        "RenglonCreate con precio_unitario",
    )
    _rechaza(
        lambda: RenglonCreate(libro_id=1, cantidad=1, subtotal="24500.00"),
        "RenglonCreate con subtotal",
    )
    _rechaza(
        lambda: VentaCreate(
            cliente_id=2,
            renglones=[{"libro_id": 1, "cantidad": 1}],
            fecha="2026-10-08T21:14:11Z",
        ),
        "VentaCreate con fecha",
    )
    _rechaza(
        lambda: VentaCreate(
            id=2,
            cliente_id=2,
            renglones=[{"libro_id": 1, "cantidad": 1}],
        ),
        "VentaCreate con id",
    )


def main() -> None:
    """Ejecuta todas las comprobaciones de contrato."""
    _editoriales()
    _generos()
    _autores()
    _libros()
    _clientes()
    _ventas()
    _altas_con_relaciones()


if __name__ == "__main__":
    main()
    print("ok")
