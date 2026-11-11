"""Registro único de los módulos que aportan modelos de tabla.

`create_all` solo crea las tablas de los modelos importados. Este módulo
concentra esos imports para que los changes posteriores agreguen tablas sin
tocar el `lifespan` de `app/main.py`.
"""

import importlib

MODEL_MODULES: tuple[str, ...] = (
    "app.modules.editoriales.models",
    "app.modules.generos.models",
    "app.modules.autores.models",
    "app.modules.libros.models",
    "app.modules.clientes.models",
    "app.modules.ventas.models",
)


def import_model_modules() -> None:
    """Importa cada módulo de modelos para que `SQLModel.metadata` los vea.

    Se ejecuta antes de `create_all`, dentro del `lifespan`. Un error de
    importación de un modelo se propaga y hace fallar el arranque, en lugar
    de crear un esquema incompleto en silencio.
    """
    for module_name in MODEL_MODULES:
        importlib.import_module(module_name)
