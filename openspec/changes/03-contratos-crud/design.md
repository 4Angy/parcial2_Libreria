# Design

## Context

Ver `proposal.md` para la motivación y `specs/` para los requisitos. El estado que condiciona el diseño:

- El change `02` dejó las nueve tablas creadas por `create_all`, con `UNIQUE` en `editorial.nombre`, `genero.nombre`, `libro.isbn`, `cliente.email` y `perfil_cliente.cliente_id`; `CHECK` nombrados en `libro`, `libro_autor`, `venta` y `renglon_venta`; claves foráneas con índice y relaciones con `back_populates`.
- `app/main.py` solo registra el router de salud. `app/core/database.py` entrega una `AsyncSession` por petición con `expire_on_commit=False`. `app/core/config.py` expone `DATABASE_URL` y `SQL_ECHO`.
- Los `schemas.py`, `service.py` y `router.py` de los seis módulos de dominio son andamiaje vacío (solo docstring). `app/modules/health/router.py` fija el estilo de router del proyecto.
- La base sembrada tiene 7 editoriales, 5 géneros, 10 autores, 9 libros, 10 autorías, 4 clientes con 4 perfiles, 2 ventas y 4 renglones. Todas las verificaciones parten de ese estado.
- Entorno local: Python 3.14, FastAPI 0.162.5, Pydantic 2.14.3, SQLModel 0.0.49, SQLAlchemy 2.1.8, asyncpg 0.32.0. La imagen de entrega usa Python 3.12 y `requirements.txt` declara mínimos, no versiones exactas.
- PostgreSQL 16.15 en `pg-libreria`, publicado en `127.0.0.1:5433`.
- La consigna fija la tabla de endpoints, las reglas RN-01 a RN-12 y los casos C-01, C-02, C-03, C-07 y C-08.

## Goals / Non-Goals

**Goals:**

- Un contrato HTTP por módulo, con DTO de alta, de actualización y de lectura separados de las tablas, y con la forma serializada que espera la consigna.
- Códigos `201`/`404`/`409`/`422` decididos en un solo lugar, sin que ningún router repita el manejo de la base.
- Paginación y traducción de errores reutilizables, no copiadas en cada endpoint.
- Lecturas con carga anticipada desde el primer día, para que `05` solo tenga que verificar el número de consultas y no reescribir los servicios.
- Verificación ejecutable contra la base real con archivos `.http` y scripts `.py`, sin dependencias nuevas.

**Non-Goals:**

- `POST /libros/` y `POST /ventas/` con DTO anidados (`04`), la copia de precio y el cálculo del total.
- La medición formal del número de consultas (C-07) y su documentación (`05`).
- `BackgroundTasks` (`06`), contenedor e imagen (`07`) y despliegue (`08`).
- Autenticación, autorización, CORS, versionado de API, borrado lógico, auditoría y migraciones.
- Envoltorios de paginación con total de filas, enlaces de página o metadatos: la consigna pide listas.
- `GET /generos/{id}` y `PATCH /generos/{id}`: la tabla de referencia no los define.

## Decisions

### 1. Inventario de DTO por módulo

Cada módulo declara sus DTO en `schemas.py`. Los `Create` no llevan `id`, los `Update` tienen todos los campos opcionales y los `Read` llevan `id` y `model_config = ConfigDict(from_attributes=True)`. Los `Create` y `Update` usan `ConfigDict(extra="forbid")`.

| Módulo | Alta | Actualización | Lectura | DTO auxiliares |
|---|---|---|---|---|
| `editoriales` | `EditorialCreate` | `EditorialUpdate` | `EditorialRead` | `EditorialRef` |
| `generos` | `GeneroCreate` | — | `GeneroRead` | `GeneroRef` |
| `autores` | `AutorCreate` | `AutorUpdate` | `AutorRead` | `AutorRef` |
| `libros` | — | `LibroUpdate` | `LibroRead` | `LibroResumenRead`, `LibroAutorRead`, `LibroDeAutorRead` |
| `clientes` | `ClienteCreate`, `PerfilCreate` | `ClienteUpdate` | `ClienteRead`, `PerfilRead` | `ClienteRef` |
| `ventas` | — | — | `VentaRead`, `RenglonRead` | `VentaResumenRead` |

- `EditorialRef`, `GeneroRef`, `AutorRef` y `ClienteRef` son variantes mínimas con `id` y el nombre visible (`nombre`, o `nombre` y `email` en el cliente). Se prefieren a reutilizar los `Read` completos porque un listado de libros no necesita `pais` ni `nacionalidad`, y porque el DTO de referencia documenta qué campos garantiza la relación.
- `LibroResumenRead` se usa en los listados y en los sublistados de editorial y género: `id`, `isbn`, `titulo`, `precio`, `stock`, `editorial` y `genero`. `LibroRead` agrega `autores` y se reserva para el detalle.
- `LibroAutorRead` representa una autoría con `autor`, `rol` y `orden`; `LibroDeAutorRead` agrega `libro` y se usa en `GET /autores/{id}/libros`, donde el recurso listado es la participación, no el libro suelto.
- `VentaResumenRead` (`id`, `fecha`, `total`) se usa en `GET /ventas/` y `GET /clientes/{id}/ventas`. No incluye renglones ni cliente para no cargar relaciones que la tabla no pide en un listado. `VentaRead` agrega `cliente` y `renglones`.
- No se define `GeneroUpdate`, `LibroCreate`, `VentaCreate` ni `RenglonCreate`: la tabla no los pide y los dos últimos pertenecen a `04`.

**Alternativas descartadas:** un único `schemas.py` global (rompe la estructura obligatoria por módulo); reutilizar los `Read` completos en todos los listados (payload más grande y relaciones que no se necesitan); exponer los modelos `table=True` como `response_model` (acopla el contrato al esquema y filtra columnas internas).

### 2. Serialización de importes, fechas y enteros

- **Importes:** Pydantic 2 serializa `Decimal` como cadena JSON y conserva la escala que devuelve `NUMERIC(10,2)`/`NUMERIC(12,2)`: `Decimal("21000.00")` sale como `"21000.00"`. No hace falta un serializador propio; se verifica en `test/serializacion.py` y se documenta como invariante del contrato. Un `float` en el DTO rompería la invariante, por eso los campos monetarios se tipan `Decimal`.
- **Fecha:** `VentaRead` y `VentaResumenRead` declaran `fecha: datetime` y un `field_serializer("fecha")` que normaliza a UTC con `astimezone(timezone.utc)`, llama a `isoformat()` y reemplaza el sufijo `+00:00` por `Z`. Así el ejemplo de la consigna (`2026-10-08T21:14:11.751581Z`) se reproduce y no depende de la zona del proceso.
- **Subtotal:** `RenglonRead` calcula `subtotal = cantidad * precio_unitario` como `Decimal`; la serialización lo emite como cadena con dos decimales, igual que el precio unitario.
- **Enteros:** `stock` y `cantidad` se tipan `int`; Pydantic los emite como números, nunca como cadenas.

**Alternativas descartadas:** `json_encoders` global (deprecado en Pydantic 2 y esconde la regla); serializar la fecha con `datetime.isoformat()` sin normalizar (deja `+00:00` o el desplazamiento de la sesión); devolver importes como `float` (prohibido por la consigna y fuente de redondeo).

### 3. PATCH parcial con `exclude_unset`

Cada `Update` declara todos sus campos con valor por defecto `None`. El servicio recibe el DTO, ejecuta `datos = dto.model_dump(exclude_unset=True)` y aplica `entidad.sqlmodel_update(datos)`. Un cuerpo `{}` produce un diccionario vacío, no modifica la entidad y devuelve `200` con el estado actual.

`exclude_unset` distingue «campo ausente» de «campo con valor nulo»: `PATCH /libros/{id}` con `{"genero_id": null}` lleva el campo a `NULL`, mientras que un cuerpo sin `genero_id` lo deja como estaba. Esa distinción es la que habilita quitar el género de un libro sin tocar el resto.

**Alternativas descartadas:** `exclude_none=True` (impide llevar un campo opcional a `NULL`); `if campo is not None: setattr(...)` (mismo problema); exigir el cuerpo completo en el `PATCH` (contradice «aplican sólo los campos enviados»).

### 4. Dependencia de paginación reutilizable

`app/core/pagination.py` define:

```python
@dataclass(frozen=True)
class Paginacion:
    limit: int
    offset: int

def paginacion(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Paginacion:
    return Paginacion(limit=limit, offset=offset)
```

Los routers la reciben con `Annotated[Paginacion, Depends(paginacion)]` y los servicios reciben el objeto, no dos enteros sueltos. FastAPI valida los parámetros antes de ejecutar el handler y responde `422` con `limit=0`, `limit=101`, `offset=-1` o valores no enteros; se comprobó con la versión instalada.

La regla se aplica a los ocho listados: `/editoriales/`, `/generos/`, `/libros/`, `/ventas/`, `/editoriales/{id}/libros`, `/generos/{id}/libros`, `/autores/{id}/libros` y `/clientes/{id}/ventas`. **Inconsistencia documentada:** la tabla de endpoints no muestra `limit`/`offset` en `/generos/` ni en los sublistados y tampoco lista `422` para ellos. RN-10 dice «todo listado», que es la regla de negocio y prevalece sobre la tabla; por eso esos endpoints aceptan paginación y pueden responder `422`. Queda anotado para la revisión del grupo.

Los listados se ordenan por clave primaria ascendente (o por `orden, libro_id` en las autorías) para que dos páginas consecutivas no repitan ni omitan filas. `GET /libros/` y los sublistados aplican `offset` y `limit` después de filtrar.

**Alternativas descartadas:** repetir `Query(ge=..., le=...)` en cada router (duplica la regla y permite que un endpoint quede sin paginar); una clase `BaseModel` como dependencia (funciona, pero mezcla un DTO con infraestructura y hace menos explícito el valor por defecto); devolver un sobre `{items, total}` (la consigna pide listas y el total agregaría una consulta que `05` contaría).

### 5. Búsqueda por título con parámetro ligado

`GET /libros/` declara `titulo: Annotated[Optional[str], Query()] = None` y `genero_id: Annotated[Optional[int], Query()] = None`. El servicio arma:

```python
consulta = select(Libro)
if titulo:
    consulta = consulta.where(Libro.titulo.ilike(f"%{titulo}%"))
if genero_id is not None:
    consulta = consulta.where(Libro.genero_id == genero_id)
```

`ilike` de SQLAlchemy se compila en PostgreSQL como `ILIKE` y envía el patrón como parámetro ligado (`$n`); el texto recibido nunca se concatena en la sentencia. El `%` se agrega en Python, no en SQL. Los caracteres `%` y `_` que escriba el usuario siguen actuando como comodines de `ILIKE`, pero eso no permite inyectar SQL: el valor completo viaja como un único parámetro y `' OR '1'='1` no encuentra coincidencias (C-08).

**Alternativas descartadas:** `text()` con f-string (inyección); `func.lower(Libro.titulo).contains(titulo.lower())` (también ligado, pero `ilike` es la forma nativa de PostgreSQL y más legible); escapar `%` y `_` (cambia la semántica de búsqueda que pide RN-11 y no es necesaria para la seguridad).

### 6. Errores de dominio y traducción centralizada de `IntegrityError`

`app/core/errors.py` concentra:

- `ErrorDeDominio(mensaje, status_code)` como base.
- `NoEncontrado(mensaje)` con `404` y `Conflicto(mensaje)` con `409`.
- `async def confirmar(session, mensaje_conflicto)`: hace `commit()`, y ante `IntegrityError` hace `rollback()` y lanza `Conflicto` desde la excepción original. El texto se elige por `SQLSTATE`, sin leer nombres de restricción: `23505` usa el mensaje de la operación (`"Ya existe una editorial con ese nombre."`, `"El ISBN ya pertenece a otro libro."`, `"El cliente ya tiene un perfil."`), `23503` usa `"La referencia indicada no existe."`, `23514` usa `"Los datos no cumplen una regla de rango."` y cualquier otro `IntegrityError` usa `"La operación viola una restricción de integridad."`.
- Un handler para `ErrorDeDominio` que responde `{"detail": mensaje}` con el código de la excepción, y un handler para `SQLAlchemyError` que responde `500` con `{"detail": "Error interno del servidor."}`. Ese handler cubre las fallas de lectura o de conexión; los `IntegrityError` ya se tradujeron a `409` en `confirmar`.

Cada operación de escritura pasa su propio mensaje de unicidad: `"Ya existe una editorial con ese nombre."`, `"Ya existe un cliente con ese correo."`, `"El cliente ya tiene un perfil."`, `"El ISBN ya pertenece a otro libro."`, etc. No se inspecciona el nombre de la restricción para elegir el texto: los nombres los genera `create_all` y podrían cambiar si se recrea el esquema, mientras que el `SQLSTATE` y el mensaje por operación son estables. El `SQLSTATE` se usa en un único punto para elegir el mensaje, pero nunca se expone.

Los routers no capturan `IntegrityError`: llaman al servicio y dejan que `NoEncontrado`/`Conflicto` lleguen al handler. Los `404` de un recurso de la ruta se lanzan desde el servicio con `NoEncontrado`. El `422` lo produce FastAPI antes del handler y su cuerpo no incluye texto de la base.

**Alternativas descartadas:** un `exception_handler` global de `IntegrityError` que adivine el mensaje por nombre de restricción (frágil y puede confundir dos reglas); `try/except` en cada router (repite la traducción y mezcla HTTP con persistencia); devolver `str(exc)` en el cuerpo (viola RN-12).

### 7. Unicidad por la base, sin consulta previa

Las altas de editorial, género, autor, cliente, libro (en `04`) y perfil escriben directamente. No hay `SELECT ... WHERE nombre = ...` ni `WHERE email = ...` antes del `INSERT`. Si el valor existe, PostgreSQL responde `23505`, `confirmar` hace `rollback` y la API devuelve `409` con el mensaje de la operación. Esto evita carreras entre dos peticiones concurrentes y cumple RN-01, RN-02 y RN-09 sin duplicar la regla en Python.

La existencia del **padre** sí se consulta cuando el contrato exige `404` y no `409`: `POST /clientes/{id}/perfil` verifica que el cliente exista antes de insertar, y los sublistados verifican que la editorial, el género, el autor o el cliente existan antes de devolver la lista. Esa consulta no es una comprobación de unicidad; es la resolución del recurso de la ruta. Si el padre se borrara entre la verificación y el `INSERT`, la clave foránea produciría `409`, que es el comportamiento aceptable para una carrera.

**Alternativas descartadas:** consultar antes de cada alta (sujeto a carreras y contradice el garante «la base»); traducir la violación de clave foránea a `404` (la consigna reserva `404` para el recurso de la ruta y `409` para el rechazo de la base).

### 8. Capas: router, servicio y contrato

- `router.py`: declara `APIRouter(prefix="/<recurso>", tags=["<recurso>"])`, las rutas, el `status_code` de las altas, `Depends(get_session)` y `Depends(paginacion)`, y el `response_model`. No contiene SQL, ni `IntegrityError`, ni cuerpos de error.
- `service.py`: funciones `async` que reciben `AsyncSession`, el DTO y/o `Paginacion`; construyen las consultas, aplican filtros, hacen `commit` mediante `confirmar` y lanzan `NoEncontrado`/`Conflicto`. No importa `HTTPException` ni conoce códigos HTTP.
- `schemas.py`: solo DTO y serializadores. No importa modelos de tabla ni servicios.
- Los servicios devuelven entidades ORM y el `response_model` del router las valida con `from_attributes=True`. Las excepciones son las altas de cliente y las lecturas con renglones: `POST /clientes/` devuelve un `ClienteRead` construido con `perfil=None` (un cliente recién creado no puede tener perfil y no se permite una carga perezosa), y `RenglonRead` aplana `libro.titulo` y calcula `subtotal` en un `model_validator(mode="before")` que acepta la entidad ORM.

**Alternativas descartadas:** servicios que devuelven `dict` (pierden el tipado y el `response_model` deja de verificar); routers que arman las consultas (impiden reutilizar la lógica en scripts de verificación); DTO dentro de `service.py` (rompe la estructura obligatoria del módulo).

### 9. Carga anticipada en las lecturas

La carga perezosa está prohibida: en una `AsyncSession`, acceder a una relación no cargada fuera del contexto greenlet lanza `MissingGreenlet`. Cada lectura declara sus opciones:

| Endpoint | Carga anticipada |
|---|---|
| `GET /libros/` | `joinedload(Libro.editorial)`, `joinedload(Libro.genero)` |
| `GET /libros/{id}` | las dos anteriores más `selectinload(Libro.autorias).joinedload(LibroAutor.autor)` |
| `GET /editoriales/{id}/libros` | `joinedload(Libro.editorial)`, `joinedload(Libro.genero)` |
| `GET /generos/{id}/libros` | ídem |
| `GET /autores/{id}/libros` | `joinedload(LibroAutor.libro)` con `joinedload(Libro.editorial)` y `joinedload(Libro.genero)` anidados |
| `GET /clientes/{id}` | `joinedload(Cliente.perfil)` |
| `GET /clientes/{id}/ventas` | ninguna: `VentaResumenRead` no expone relaciones |
| `GET /ventas/` | ninguna: `VentaResumenRead` no expone relaciones |
| `GET /ventas/{id}` | `joinedload(Venta.cliente)`, `selectinload(Venta.renglones).joinedload(RenglonVenta.libro)` |

Se usa `joinedload` para relaciones a-uno y `selectinload` para colecciones, de modo que el detalle de un libro con varios autores o de una venta con varios renglones no multiplique filas ni consulte por elemento. `GET /libros/{id}` y `GET /ventas/{id}` no necesitan `unique()` porque la colección se carga con `selectinload`; si un futuro endpoint usara `joinedload` sobre una colección, deberá aplicar `unique()`.

`GET /clientes/{id}` devuelve `perfil` como objeto o `null`: el modelo ya declara `uselist: False` y `joinedload` respeta esa cardinalidad, así que el DTO nunca recibe una lista.

**Alternativas descartadas:** `lazy="selectin"` global en los modelos (carga relaciones que el endpoint no usa y obliga a tocar `02`); cargar relaciones con consultas separadas por id (N+1 y lo que `05` debe evitar); `lazy="raise"` (haría fallar los endpoints que hoy no cargan una relación, aunque no la serialicen).

### 10. Registro de routers en `app/main.py`

`app/main.py` importa los seis routers de dominio y los incluye sin prefijo adicional, porque cada router ya declara su `prefix`:

```python
app.include_router(health_router, prefix="/health")
app.include_router(editoriales_router)
app.include_router(generos_router)
app.include_router(autores_router)
app.include_router(libros_router)
app.include_router(clientes_router)
app.include_router(ventas_router)
```

Se elige `main.py` y no un `app/api.py` nuevo porque `project-structure` asigna el registro de routers a `app/main.py` y la consigna no lista un archivo adicional. La lista es explícita: agregar un módulo futuro obliga a decidir si se publica, en lugar de descubrirlo por importación implícita. El `lifespan` no se toca.

Las rutas de colección se declaran con `"/"`; FastAPI redirige `GET /editoriales` a `/editoriales/` con `307`. Los archivos `.http` usan siempre la barra final. Los métodos no definidos sobre una ruta existente (por ejemplo `PATCH /ventas/{id}` o `POST /libros/`) responden `405`.

**Alternativas descartadas:** un `app/api.py` con un router agregador (agrega un archivo que la estructura no pide y una indirección sin beneficio en seis routers); descubrimiento automático de routers (oculta qué se publica y complica el arranque).

### 11. Transacciones y estado de la sesión

Cada petición recibe su sesión de `get_session` y cada escritura hace un único `commit` a través de `confirmar`. Con `expire_on_commit=False`, los atributos del objeto siguen disponibles después del `commit` y el `201` no necesita un `refresh`. Cuando la respuesta incluye relaciones (`PATCH /libros/{id}`, `PATCH /clientes/{id}`), el servicio vuelve a leer la entidad con las mismas opciones de carga anticipada que el `GET` correspondiente, porque las relaciones no se actualizan solas tras el `commit`. Si el `commit` falla, `confirmar` hace `rollback` y la sesión queda descartable; la petición siguiente usa una sesión nueva.

**Alternativas descartadas:** `expire_on_commit=True` (obliga a un `refresh` por escritura y puede disparar cargas perezosas); `commit` en el router (mezcla transporte con persistencia y duplica el manejo del error).

### 12. Verificación sin `pytest`

- `test/contratos.http`: altas, lecturas, `PATCH` parcial, cuerpo vacío y códigos por módulo, con la respuesta esperada en un comentario. Incluye `GET /health/live` y `/health/ready` para demostrar que `01` sigue vigente.
- `test/paginacion.http`: límites por defecto, `limit=2` con dos páginas, `limit=0`, `limit=101`, `offset=-1`, búsqueda parcial, C-08 y filtro por género.
- `test/errores.http`: C-01 (`/editoriales/abc`), `404`, C-02 (editorial y email repetidos), C-03 (segundo perfil) y comprobación de que el cuerpo no contiene `23505`, `_key`, `duplicate key` ni nombres de tabla.
- `test/lecturas.http`: detalle de libro con editorial, género y autores; detalle de venta con cliente y renglones con `subtotal`; cliente con `perfil` objeto y cliente sin perfil con `null`.
- `test/serializacion.py`: ejecutable con `.venv\Scripts\python.exe`; valida con `model_dump(mode="json")` que `Decimal` sale como cadena, la fecha termina en `Z`, `stock`/`cantidad` son enteros y `RenglonRead` aplana `titulo` y calcula `subtotal` a partir de una entidad ORM construida en el propio script.
- `test/consultas.py`: ejecutable con `.venv\Scripts\python.exe`; conecta con `DATABASE_URL`, registra las sentencias con un evento `before_cursor_execute`, ejecuta la búsqueda de `listar_libros` con el texto de C-08 y afirma que la sentencia usa `ILIKE $n` y que el valor viaja en `parameters`, no en el texto. También imprime la sentencia para contrastarla con `SQL_ECHO=true`.
- `test/rutas.py`: ejecutable con `.venv\Scripts\python.exe`; arma el inventario desde `app.openapi()["paths"]` (en FastAPI 0.162.5 los routers incluidos aparecen en `app.routes` como `_IncludedRouter`, sin `path` ni `methods`) y lo compara con las rutas de la tabla de referencia, incluidas las ausencias deliberadas de `04` (`POST /libros/`, `POST /ventas/`).

Los `.http` se ejecutan contra `uvicorn app.main:app --port 8000` con la base sembrada. Los casos que escriben usan datos con el prefijo `Prueba 03` y el archivo documenta el bloque SQL de limpieza para poder repetirlos (el change no expone endpoints `DELETE`, así que la limpieza se ejecuta con `docker exec pg-libreria psql -U libreria -d libreria -c "..."`); los `PATCH` sobre datos sembrados restauran el valor original. No se agrega `pytest` ni ninguna dependencia: los scripts usan `assert` y terminan con código distinto de cero si fallan.

**Alternativas descartadas:** `pytest` (dependencia nueva y fuera del stack); `TestClient` para todo (arranca el `lifespan` y la base, pero no demuestra el contrato HTTP tal como lo ve un cliente); depender de `curl` (los `.http` son la convención del proyecto).

### 13. Compatibilidad con Python 3.12

Se usa `typing.Optional`, `list[...]`, `Annotated`, `dataclass` y `datetime.timezone.utc`. No se usan alias `type`, genéricos PEP 695, `Self`, `StrEnum` ni sintaxis de 3.13/3.14. `from __future__ import annotations` solo se usa si un módulo lo necesita; los DTO de Pydantic se evalúan en tiempo de definición y no dependen de anotaciones diferidas. La comprobación definitiva se repite en `07` dentro de `python:3.12-alpine`.

**Alternativas descartadas:** aprovechar características de 3.14 del entorno local (la imagen de entrega no las soporta).

## Risks / Trade-offs

- **Paginación en endpoints que la tabla no pagina:** `/generos/` y los sublistados aceptan `limit`/`offset` y pueden devolver `422`, aunque la tabla solo liste `200`. → Se sigue RN-10, se documenta la diferencia acá y se repite en la revisión del grupo; si el corrector prefiere la tabla, quitar la dependencia de esos routers es un cambio local.
- **Mensaje de `409` por operación, no por restricción:** dos reglas distintas sobre la misma escritura devolverían el mismo texto. → Hoy cada escritura viola una sola regla de unicidad; si se agrega otra, el mensaje se ajusta en el servicio. No se parsean nombres de restricción generados por `create_all`.
- **`409` para violaciones de `CHECK`:** el DTO atrapa `precio <= 0` y `stock < 0` con `422`, pero una escritura que llegue a la base devuelve `409`. → Es la lectura literal de «409 si la base rechaza la escritura»; ambos códigos están documentados y el `422` es el camino normal.
- **Wildcards en `titulo`:** `%` y `_` del usuario funcionan como comodines. → No hay inyección porque el valor es un parámetro ligado; se documenta y no se escapa para no cambiar la semántica de «parte del título».
- **`ilike` y acentos:** la comparación no ignora acentos (`cancion` no encuentra `canción`). → RN-11 solo pide ignorar mayúsculas; si el corrector pide acentos, se resuelve con `unaccent` o una columna normalizada en otro change.
- **Redirección `307` por barra final:** un cliente que llame `/editoriales` recibe una redirección. → Los `.http` usan la barra final; se documenta en el README de pruebas si aparece la duda.
- **Secuencias con huecos:** un `POST` que termina en `409` consume un valor de secuencia. → Ninguna prueba asume ids contiguos; las verificaciones usan los ids devueltos por la API o los de la semilla.
- **Datos de prueba persistentes:** los `.http` crean filas. → Prefijo `Prueba 03` y bloque SQL de limpieza documentado; los `PATCH` restauran el valor original.
- **Relaciones desactualizadas tras el `commit`:** `expire_on_commit=False` conserva el estado viejo de una relación. → Los `PATCH` que devuelven relaciones vuelven a leer la entidad con carga anticipada.
- **Python local 3.14 vs. imagen 3.12:** una construcción válida en local podría no serlo en la imagen. → Solo se usan características de 3.12 y la comprobación se repite en `07`.

## Migration Plan

No hay cambios de esquema ni migraciones. Para aplicar y verificar:

1. Arrancar `pg-libreria` y confirmar que la base sembrada responde (`docker start pg-libreria` si hace falta).
2. Ejecutar `uvicorn app.main:app --port 8000` con el `.env` del proyecto.
3. Ejecutar los archivos `.http` en este orden: `contratos`, `paginacion`, `errores`, `lecturas`.
4. Ejecutar `.venv\Scripts\python.exe test\serializacion.py`, `.venv\Scripts\python.exe test\consultas.py`, `.venv\Scripts\python.exe test\errores_integridad.py` y `.venv\Scripts\python.exe test\rutas.py`.
5. Repetir `test/paginacion.http` con `SQL_ECHO=true` para ver el parámetro ligado en la consola.

Rollback: revertir el commit de implementación deja los `schemas.py`, `service.py` y `router.py` como andamiaje y `app/main.py` sin los seis routers. La base no cambia; las filas creadas por las pruebas se eliminan con el bloque SQL documentado en `test/contratos.http`.

## Open Questions

- La forma exacta de `GET /autores/{id}/libros` (`LibroDeAutorRead` con `libro` anidado) es una decisión de contrato que la consigna no ejemplifica; si el corrector espera los campos del libro al mismo nivel que `rol` y `orden`, se aplana el DTO sin cambiar los servicios ni las specs.
- `GET /generos/{id}` no está en la tabla y no se implementa. Si aparece la necesidad de consultar un género suelto, se agrega en un change posterior con su propio requisito.
