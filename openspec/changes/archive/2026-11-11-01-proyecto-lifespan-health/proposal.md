# Proposal

## Why

El parcial «Unidad 1 a 4 · Del objeto a la persistencia» exige un proyecto FastAPI asincrónico con una estructura de carpetas obligatoria, configuración por entorno y recursos de base de datos creados en el ciclo de vida de la aplicación. Sin esa base —motor, fábrica de sesiones, dependencia `get_session`, creación del esquema al arrancar y rutas de salud— ningún change posterior (modelos, CRUD, altas, lecturas, contenedor) puede implementarse ni verificarse. Este change establece ese cimiento y cubre el criterio «Proyecto, conexión y ciclo de vida» (8 % de la nota).

## What Changes

- Se crea el esqueleto del proyecto con la estructura obligatoria: `app/main.py`, `app/core/config.py`, `app/core/database.py`, `app/modules/<módulo>/` y `test/`.
- Se agrega `requirements.txt` con las versiones mínimas del stack (FastAPI, SQLModel, SQLAlchemy asincrónico, asyncpg, python-dotenv, uvicorn).
- La configuración lee `DATABASE_URL` y `SQL_ECHO` del entorno mediante `python-dotenv`; **no existe ningún valor por defecto para `DATABASE_URL`**. Si falta, el arranque falla y el proceso termina con error.
- El `lifespan` de `app/main.py` crea el motor asincrónico y la fábrica de sesiones, los publica en `app.state`, crea las tablas faltantes con `SQLModel.metadata.create_all` y cierra el motor al apagar.
- Se deja un punto único de registro de modelos (`app/core/registry.py`) para que `create_all` vea los modelos de los changes siguientes sin modificar el `lifespan`. En este change importa los seis módulos de dominio, cuyos `models.py` existen vacíos como andamiaje.
- `app/core/database.py` expone la dependencia `get_session`, que entrega una sesión por petición con `expire_on_commit=False`.
- Se implementan los módulos mínimos `health`, `editoriales`, `generos`, `autores`, `libros`, `clientes` y `ventas` con la estructura de carpetas exigida; en este change solo `health` tiene contenido funcional y el resto queda como andamiaje sin lógica de dominio.
- Se exponen `GET /health/live` (sin tocar la base) y `GET /health/ready` (`SELECT 1` contra la base).
- Se agrega `test/health.http` con los casos de salud y su resultado esperado en comentarios.

**Fuera de alcance:** modelos de tabla del dominio y script de datos iniciales (`02`), DTO y CRUD (`03`), altas con relaciones (`04`), carga anticipada (`05`), `BackgroundTasks` (`06`), `Dockerfile` y `.dockerignore` (`07`), `DEPLOY.md` y despliegue (`08`), `README.md` y carpeta `evidencia/` (se completan al cierre del proyecto).

## Capabilities

### New Capabilities

- `project-structure`: estructura obligatoria de carpetas y módulos, punto único de registro de modelos y dependencias del proyecto declaradas en `requirements.txt`.
- `runtime-lifecycle`: configuración por entorno, creación y cierre del motor asincrónico, fábrica de sesiones, dependencia `get_session` por petición, creación del esquema al arrancar y fallo de arranque ante configuración faltante.
- `health-checks`: rutas de salud `live` y `ready`, con y sin dependencia de la base.

### Modified Capabilities

- Ninguna: el proyecto no tiene specs previas.

## Impact

- **Código nuevo:** `app/__init__.py`, `app/main.py`, `app/core/config.py`, `app/core/database.py`, `app/core/registry.py`, `app/modules/__init__.py`, los paquetes de los siete módulos mínimos y `app/modules/health/router.py`.
- **Configuración:** `requirements.txt`, `test/health.http`. Se reutilizan `env.example` y `.gitignore` ya existentes; no se modifican.
- **API:** `GET /health/live` y `GET /health/ready`.
- **Dependencias:** FastAPI ≥ 0.111, SQLModel ≥ 0.0.24, SQLAlchemy 2.0 asincrónico, asyncpg ≥ 0.30, python-dotenv ≥ 1.0, uvicorn (incluido en `fastapi[standard]`).
- **Riesgos:** el arranque depende de una base PostgreSQL 16 accesible; sin `DATABASE_URL` o sin base, el proceso no queda sirviendo por diseño. La sintaxis debe ser compatible con Python 3.12, aunque el entorno local tenga 3.14.
- **Changes posteriores:** `02` completa `models.py` y el registro; `03` completa `schemas.py`, `service.py` y `router.py` del resto de los módulos; `07` y `08` agregan el contenedor y el despliegue.
