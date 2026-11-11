# Design

## Context

Proyecto nuevo, sin código de aplicación todavía. El repositorio ya tiene `openspec/`, `.gitignore`, `env.example` y la consigna en `docs/`. El stack y la estructura están fijados por la consigna; ver `proposal.md` para la motivación y `specs/` para los requisitos.

Restricciones que condicionan el diseño:

- La imagen de entrega parte de `python:3.12-alpine`; el entorno local tiene Python 3.14. El código no puede usar sintaxis exclusiva de 3.13 o 3.14.
- `SQLModel.metadata.create_all` solo crea tablas que faltan: no hay migraciones en el alcance.
- `DATABASE_URL` no tiene valor por defecto y su ausencia debe impedir el arranque.
- Los changes `02` a `08` van a completar los módulos; este change debe dejar el mecanismo listo sin adelantar su lógica.

## Goals / Non-Goals

**Goals:**

- Dejar un esqueleto ejecutable: arranca, crea el esquema y responde las dos sondas de salud.
- Aislar la configuración, el motor y la sesión en `app/core/`, de modo que los módulos de dominio no conozcan detalles de conexión.
- Dejar un único punto de registro de modelos para que `02` agregue tablas sin tocar `app/main.py`.
- Fijar la convención de módulos para que `03` a `06` solo agreguen contenido.

**Non-Goals:**

- Modelos de tabla del dominio, DTO, CRUD, paginación, altas con relaciones, carga anticipada y `BackgroundTasks`.
- Script de datos iniciales, `Dockerfile`, `.dockerignore`, `DEPLOY.md`, `README.md` y `evidencia/`.
- Migraciones de esquema y autenticación.

## Decisions

### 1. Configuración con `python-dotenv` y un objeto de settings propio

`app/core/config.py` carga `.env` con `load_dotenv()` y expone `get_settings()`, que devuelve un `dataclass` inmutable con `database_url` y `sql_echo`.

- `DATABASE_URL` se lee de `os.environ` sin valor por defecto. Si falta o está vacía, `get_settings()` lanza `RuntimeError` con un mensaje que nombra la variable y no incluye credenciales.
- `SQL_ECHO` se interpreta como booleano y vale `false` cuando falta o no es un valor verdadero.
- Se cachea con `functools.lru_cache` para no releer el entorno en cada llamada.

**Alternativas descartadas:** `pydantic-settings` (no está en el stack de la consigna y agrega una dependencia); leer `os.environ` directamente en cada módulo (dispersa la validación y permite valores por defecto accidentales).

### 2. `lifespan` como único dueño del motor y de la fábrica de sesiones

`app/main.py` define un `asynccontextmanager` que, en orden:

1. Obtiene la configuración (falla acá si falta `DATABASE_URL`).
2. Importa el registro de modelos.
3. Crea el motor con `create_async_engine(settings.database_url, echo=settings.sql_echo)`.
4. Crea `async_sessionmaker(engine, expire_on_commit=False)`.
5. Publica ambos en `app.state.engine` y `app.state.session_factory`.
6. Ejecuta `SQLModel.metadata.create_all` con `await conn.run_sync(...)` dentro de `engine.begin()`.
7. En el `finally`, llama a `await engine.dispose()`.

La creación dentro del `lifespan` (y no al importar el módulo) permite que un fallo de configuración o de base se registre como error de arranque y que uvicorn termine el proceso, que es el comportamiento que pide D-05. También garantiza que el motor se cree una sola vez por proceso.

**Alternativas descartadas:** motor global creado al importar `database.py` (no se cierra de forma ordenada y mezcla configuración con importación); crear el motor por petición (desperdicia el pool y no cumple la consigna).

### 3. `get_session` como dependencia por petición

`app/core/database.py` define `get_session(request: Request)` como generador asincrónico:

- Lee `request.app.state.session_factory`.
- Abre `async with session_factory() as session: yield session`.
- El contexto cierra la sesión al terminar la petición, incluso si el handler lanza una excepción.

La fábrica ya trae `expire_on_commit=False`, así que los handlers pueden leer atributos después del `commit` sin una consulta extra ni un `MissingGreenlet`.

**Alternativas descartadas:** sesión global compartida (una petición vería cambios de otra); `Depends` que devuelve la fábrica y obliga a cada handler a abrir el contexto (repite código y permite olvidos).

### 4. Registro único de modelos en `app/core/registry.py`

`registry.py` declara una tupla con los módulos que aportan modelos y los importa con `importlib.import_module`:

```python
MODEL_MODULES = (
    "app.modules.editoriales.models",
    "app.modules.generos.models",
    "app.modules.autores.models",
    "app.modules.libros.models",
    "app.modules.clientes.models",
    "app.modules.ventas.models",
)
```

En este change esos `models.py` existen vacíos como andamiaje. `02` los completa y `create_all` los ve sin cambios en el `lifespan` ni en el registro. `health` no aparece porque no tiene tablas.

**Alternativas descartadas:** importar cada modelo dentro de `main.py` (obliga a editar el ciclo de vida en cada change); usar `pkgutil` para descubrir módulos automáticamente (importa código por efecto secundario y oculta errores de importación).

### 5. Andamiaje de módulos y excepción de `health`

Se crean los paquetes `app/modules/{editoriales,generos,autores,libros,clientes,ventas}` con `models.py`, `schemas.py`, `service.py` y `router.py` vacíos (solo docstring que indica el change que los completa). Así la estructura obligatoria existe desde el primer commit y los changes posteriores no crean rutas nuevas, solo contenido.

`health` es la excepción: solo tiene `router.py`, porque no persiste nada, no tiene DTO ni reglas de negocio. Un `service.py` vacío o un `models.py` sin tabla serían archivos decorativos que sugerirían una responsabilidad inexistente. La excepción queda documentada acá y en el docstring del módulo.

`app/main.py` registra únicamente el router de `health` con prefijo `/health`. Los routers de dominio se registran en `03`, cuando tengan rutas.

### 6. Sondas de salud

- `GET /health/live` es un handler `async def` que devuelve `{"estado": "vivo"}` con `200`, sin dependencia de sesión.
- `GET /health/ready` recibe `Depends(get_session)`, ejecuta `SELECT 1` con `text("SELECT 1")` y devuelve `{"estado": "listo", "base": "disponible"}` con `200`.
- Si la consulta falla, captura `SQLAlchemyError` y responde `503` con `{"estado": "no_listo", "base": "no_disponible"}`, sin el texto del error.

**Alternativas descartadas:** usar el motor de `app.state` directamente en `ready` (no demuestra la dependencia de sesión); devolver `500` ante base caída (un orquestador no distingue un error de código de una dependencia no disponible).

### 7. Dependencias y compatibilidad

`requirements.txt` declara mínimos, sin fijar versiones exactas: `fastapi[standard]>=0.111`, `sqlmodel>=0.0.24`, `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.30`, `python-dotenv>=1.0`. `uvicorn` llega con `fastapi[standard]`.

El código se limita a sintaxis de Python 3.12: sin parámetros de tipo PEP 695, sin `type` alias, sin `asyncio.timeout` con características nuevas. Se usa `from __future__ import annotations` solo si aporta claridad, no como sustituto de compatibilidad.

### 8. Pruebas HTTP

`test/health.http` contiene, como mínimo:

- `GET /health/live` con `200` y `{"estado": "vivo"}` esperados.
- `GET /health/ready` con `200` y base disponible.
- `GET /health/ready` con base detenida, esperado `503` (comentado como caso manual).
- Arranque sin `DATABASE_URL`, con el comando y el resultado esperado (proceso termina con error).

Cada caso lleva el resultado esperado en un comentario, como pide la consigna.

## Risks / Trade-offs

- **`create_all` no migra:** un cambio de modelo no llega a una base existente. → Se documenta en el código y en `DEPLOY.md` (`08`); para desarrollo se recrea la base. Es una decisión de la consigna, no un defecto.
- **Base inaccesible al arrancar:** el proceso no levanta, por diseño. → El arranque falla con un mensaje claro y `--restart unless-stopped` en el despliegue (`07`/`08`) reintenta.
- **`expire_on_commit=False`:** los objetos pueden quedar con datos viejos si otra transacción los modifica. → Es el comportamiento exigido; las lecturas de detalle se harán con consultas explícitas en `05`.
- **Python local 3.14 vs. imagen 3.12:** una construcción válida en local podría no serlo en la imagen. → Solo se usan características de 3.12; la verificación final se hace construyendo la imagen en `07`.
- **Archivos de andamiaje vacíos:** pueden confundirse con módulos implementados. → Cada archivo lleva un docstring que indica qué change lo completa; `tasks.md` enumera qué queda pendiente.
- **Código de `503` en `ready` no está fijado por la consigna:** la tabla de endpoints solo lista `200`. → Se elige `503` por semántica HTTP y se deja registrado como supuesto en la entrega.

## Migration Plan

No hay datos ni despliegue previos. Para levantar en desarrollo:

1. Crear el entorno virtual e instalar `requirements.txt`.
2. Copiar `env.example` a `.env` y completar `DATABASE_URL` con el driver `postgresql+asyncpg`.
3. Iniciar PostgreSQL 16 y ejecutar `uvicorn app.main:app --reload`.
4. Verificar `GET /health/live` y `GET /health/ready`.

Rollback: al ser un proyecto nuevo, revertir el commit de implementación elimina todo el change. No hay migraciones que deshacer.
