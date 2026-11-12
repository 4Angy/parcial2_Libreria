"""Inventario de rutas del change 04 contra la tabla de endpoints.

En FastAPI 0.162.5 los routers incluidos aparecen en `app.routes` como
`_IncludedRouter` sin `path` ni `methods`, así que el inventario se arma desde
`app.openapi()["paths"]` (métodos en minúscula). Se comparan las rutas
publicadas con las 26 de la tabla de referencia y se comprueban las ausencias
deliberadas del change.
"""

import sys
from pathlib import Path

# Permite ejecutar el archivo directamente sin depender de PYTHONPATH.
_RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(_RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROYECTO))

from app.main import app  # noqa: E402

REQUERIDAS = {
    ("get", "/health/live"),
    ("get", "/health/ready"),
    ("post", "/editoriales/"),
    ("get", "/editoriales/"),
    ("get", "/editoriales/{id}"),
    ("patch", "/editoriales/{id}"),
    ("get", "/editoriales/{id}/libros"),
    ("post", "/generos/"),
    ("get", "/generos/"),
    ("get", "/generos/{id}/libros"),
    ("post", "/autores/"),
    ("get", "/autores/{id}"),
    ("patch", "/autores/{id}"),
    ("get", "/autores/{id}/libros"),
    ("get", "/libros/"),
    ("post", "/libros/"),
    ("get", "/libros/{id}"),
    ("patch", "/libros/{id}"),
    ("post", "/clientes/"),
    ("get", "/clientes/{id}"),
    ("patch", "/clientes/{id}"),
    ("post", "/clientes/{id}/perfil"),
    ("get", "/clientes/{id}/ventas"),
    ("get", "/ventas/"),
    ("post", "/ventas/"),
    ("get", "/ventas/{id}"),
}

AUSENTES = {
    ("patch", "/ventas/{id}"),
    ("patch", "/generos/{id}"),
    ("get", "/autores/"),
}

esquema = app.openapi()
publicadas = {
    (metodo, ruta)
    for ruta, operaciones in esquema["paths"].items()
    for metodo in operaciones
}

faltan = REQUERIDAS - publicadas
sobran = publicadas - REQUERIDAS
print(f"faltan {faltan} sobran {sobran}")

assert len(REQUERIDAS) == 26, f"la tabla de referencia tiene 26 rutas, no {len(REQUERIDAS)}"
assert not faltan, f"faltan rutas requeridas: {sorted(faltan)}"
assert not sobran, f"sobran rutas no previstas: {sorted(sobran)}"

for ausente in AUSENTES:
    assert ausente not in publicadas, f"la ruta {ausente} no debería publicarse"

assert not any(metodo in ("put", "delete") for metodo, _ in publicadas), (
    "el change no publica PUT ni DELETE"
)

print("ok")
