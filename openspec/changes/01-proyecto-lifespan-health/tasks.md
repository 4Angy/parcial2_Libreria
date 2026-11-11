# Tasks

## 1. Esqueleto del proyecto y dependencias

- [x] 1.1 Crear los paquetes base (`app/`, `app/core/`, `app/modules/`) y el andamiaje de los siete módulos mínimos: `editoriales`, `generos`, `autores`, `libros`, `clientes` y `ventas` con `__init__.py` y con `models.py`, `schemas.py`, `service.py` y `router.py` vacíos (solo docstring que indica el change que los completa); `health` solo con `__init__.py` y `router.py`. Verificación: `python -c "import app.modules.editoriales.models, app.modules.generos.models, app.modules.autores.models, app.modules.libros.models, app.modules.clientes.models, app.modules.ventas.models; print('ok')"` imprime `ok` y `Get-ChildItem app\modules -Recurse -Filter *.py` muestra las rutas de la consigna.

- [x] 1.2 Declarar `requirements.txt` con `fastapi[standard]>=0.111`, `sqlmodel>=0.0.24`, `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.30` y `python-dotenv>=1.0`. Verificación: en un entorno virtual nuevo, `pip install -r requirements.txt` termina sin errores y `pip check` informa que no hay dependencias rotas.

## 2. Configuración, motor y sesión

- [x] 2.1 Implementar `app/core/config.py`: cargar `.env` con `load_dotenv()`, exponer `get_settings()` con `database_url` y `sql_echo`, sin valor por defecto para `DATABASE_URL` y con `SQL_ECHO` en `false` cuando falta. Verificación: con `DATABASE_URL` definida, `python -c "from app.core.config import get_settings; print(get_settings())"` muestra la dirección y el diagnóstico; sin `DATABASE_URL` ni `.env`, el mismo comando termina con `RuntimeError` que nombra la variable; con `SQL_ECHO=true`, la configuración devuelve `True`.

- [x] 2.2 Implementar `app/core/database.py` con la dependencia `get_session`, que toma `request.app.state.session_factory`, abre una sesión por petición y la cierra al terminar. Verificación: `python -c "import inspect; from app.core.database import get_session; src=inspect.getsource(get_session); assert inspect.isasyncgenfunction(get_session) and 'session_factory' in src and 'async with' in src; print('ok')"` imprime `ok`; el uso real de la dependencia se comprueba en la tarea 4.1.

- [x] 2.3 Implementar `app/core/registry.py` con la tupla `MODEL_MODULES` y la función que importa cada `models.py` de dominio antes de `create_all`. Verificación: `python -c "from app.core.registry import MODEL_MODULES, import_model_modules; import_model_modules(); print(len(MODEL_MODULES))"` imprime `6` sin errores de importación.

## 3. Ciclo de vida de la aplicación

- [ ] 3.1 Implementar `app/main.py` con el `lifespan`: obtener la configuración, importar el registro de modelos, crear el motor y la fábrica con `expire_on_commit=False`, publicarlos en `app.state.engine` y `app.state.session_factory`, ejecutar `SQLModel.metadata.create_all` con `run_sync` y cerrar el motor con `dispose()` al apagar; registrar el router de `health`. Verificación: con la base arriba, `python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); c.__enter__(); print(bool(app.state.engine), bool(app.state.session_factory)); c.__exit__(None,None,None)"` imprime `True True` y cierra sin error; `uvicorn app.main:app` arranca sin errores de conexión ni de importación.

- [x] 3.2 Verificar el arranque sin dirección de base (caso D-05). Verificación: sin `DATABASE_URL` en el entorno ni en `.env`, `uvicorn app.main:app --port 8000` termina con código de salida distinto de cero, imprime el error de la variable faltante y `Test-NetConnection 127.0.0.1 -Port 8000` falla; el proceso no queda escuchando.

- [ ] 3.3 Verificar el cierre ordenado del motor. Verificación: con la aplicación arriba, contar las conexiones con `SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()`; detener uvicorn con `Ctrl+C` y repetir la consulta: el número vuelve al valor previo y no quedan conexiones de la aplicación.

## 4. Rutas de salud

- [ ] 4.1 Implementar `app/modules/health/router.py` con `GET /health/live` (`async def`, sin base, `{"estado": "vivo"}`, 200) y `GET /health/ready` (`async def`, `Depends(get_session)`, `SELECT 1`, 200 con `{"estado": "listo", "base": "disponible"}`; ante fallo de base, 503 con `{"estado": "no_listo", "base": "no_disponible"}` sin texto interno). Verificación: `curl.exe -i http://127.0.0.1:8000/health/live` devuelve 200 y el cuerpo esperado; `curl.exe -i http://127.0.0.1:8000/health/ready` devuelve 200 con la base arriba; con `SQL_ECHO=true`, la consola muestra la consulta `SELECT 1`; al detener PostgreSQL, `live` sigue en 200 y `ready` devuelve 503 sin detalles internos.

- [x] 4.2 Crear `test/health.http` con los casos de salud y el resultado esperado en comentarios: `live` 200, `ready` 200 con base arriba, `ready` 503 con base caída y arranque sin `DATABASE_URL` con el comando y el error esperado. Verificación: ejecutar cada caso con el cliente HTTP del IDE y comparar la respuesta con su comentario; el archivo contiene los cuatro casos con su resultado esperado.

## 5. Integración

- [ ] 5.1 Reconstruir el proyecto desde cero siguiendo el diseño: crear `.venv`, instalar `requirements.txt`, copiar `env.example` a `.env` con una base PostgreSQL 16 real y arrancar con `uvicorn app.main:app`. Verificación: el arranque termina sin error, `GET /health/live` y `GET /health/ready` responden 200, y la consola muestra el arranque completo.

- [x] 5.2 Revisar compatibilidad con Python 3.12. Verificación: `python -m compileall -q app` no reporta errores y `Get-ChildItem app -Recurse -Filter *.py | Select-String -Pattern "^type \w+ =|def \w+\[|class \w+\["` no devuelve coincidencias (sin alias `type` ni parámetros de tipo PEP 695); la comprobación definitiva se repite en el change `07` dentro de `python:3.12-alpine`.

- [x] 5.3 Confirmar que el change no invadió los changes siguientes. Verificación: `Test-Path Dockerfile, .dockerignore, DEPLOY.md, README.md, evidencia` devuelve `False` para todas las rutas y los `models.py` de dominio siguen sin clases de tabla (`Select-String -Path app\modules\*\models.py -Pattern "class .*\(SQLModel\)"` no devuelve coincidencias).

## Workflow follow-up

- Archivar el change después de la revisión del grupo.
- Verificar el resultado archivado contra `openspec/specs/`.
