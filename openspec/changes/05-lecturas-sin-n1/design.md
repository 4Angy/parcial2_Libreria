# Design

## Context

Ver `proposal.md` para la motivación y `specs/eager-loading/spec.md` para los requisitos. El estado que condiciona este diseño:

- Los changes `01` a `04` están archivados y sus specs promovidas. `openspec list` no tiene changes activos: este es el único.
- La carga anticipada ya existe y no se reescribe. `app/modules/libros/service.py` tiene `_consulta_libro()` con `joinedload(Libro.editorial)`, `joinedload(Libro.genero)` y `selectinload(Libro.autorias).joinedload(LibroAutor.autor)`, usado por `obtener_libro`, `_releer_libro` (con `populate_existing=True`) y `crear_libro`; `listar_libros` carga solo editorial y género y devuelve `LibroResumenRead`.
- `app/modules/ventas/service.py` tiene `_consulta_venta()` con `joinedload(Venta.cliente)` y `selectinload(Venta.renglones).joinedload(RenglonVenta.libro)`, usado por `obtener_venta`, `_releer_venta` y `crear_venta`; `listar_ventas` no declara opciones y devuelve `VentaResumenRead`.
- `app/modules/clientes/service.py` usa `joinedload(Cliente.perfil)`; `listar_ventas_de_cliente` resuelve el cliente con `session.get` y lista ventas sin opciones. `editoriales/service.py` y `generos/service.py` cargan editorial y género en sus sublistados de libros; `autores/service.py` carga `LibroAutor.libro` con editorial y género.
- `Libro.autorias` es `Relationship(back_populates="libro")` sin `order_by`; `Venta.renglones` es `Relationship(back_populates="venta", sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True})` sin `order_by`. `LibroAutor` tiene PK `(libro_id, autor_id)`, `rol` y `orden` con `CHECK orden >= 1`; `RenglonVenta.id` es PK autoincremental.
- `test/consultas.py` ya demuestra, para el libro 1 y la venta 1, que la serialización funciona con la sesión y el motor cerrados. `test/altas_relaciones.py` ya fija en tres los `SELECT` del alta de venta. `test/rutas.py` exige 26 rutas y no cambia. Los cinco `.http` de dominio están en verde.
- Base sembrada: `editorial=7, genero=5, autor=10, libro=9, libro_autor=10, cliente=4, perfil_cliente=4, venta=2, renglon_venta=4`. Los nueve libros tienen al menos una autoría; las dos ventas tienen dos renglones cada una.
- Entorno local: Python 3.14, SQLAlchemy **2.1.8**, SQLModel 0.0.49, FastAPI 0.162.5, Pydantic 2.14.3, PostgreSQL 16.15 en `pg-libreria` (`127.0.0.1:5433`). La imagen de entrega usa Python 3.12 y `requirements.txt` declara mínimos (`sqlalchemy[asyncio]>=2.0`), no versiones exactas.
- El `design.md` archivado de `03` fija las capas, los DTO, `Decimal` como cadena, la fecha UTC con `Z`, `PATCH` con `exclude_unset`, la paginación, `app/core/errors.py`, la carga anticipada y la verificación sin `pytest`. El del `04` fija la relectura con `populate_existing=True`, el precio copiado y el total calculado. Este change los respeta y no los contradice.

**Medición previa.** Antes de fijar el contrato se midió la implementación actual contra la base real con un evento `before_cursor_execute`, en sesiones nuevas por lectura. El resultado está en la decisión 1 y es la base de la decisión 2.

## Goals / Non-Goals

**Goals:**

- Convertir la carga anticipada existente en un criterio verificable: `joinedload` para a-uno, `selectinload` para colecciones y número fijo de consultas en los dos detalles.
- Cerrar los dos huecos reales: el orden de `autores` y de `renglones` no era estable y no había una prueba que midiera C-07.
- Demostrar con evidencia ejecutable que la cantidad de consultas no crece con la cantidad de hijos y que la serialización no depende de la carga perezosa.
- Mantener el contrato HTTP, las rutas, los DTO y la base sin cambios.

**Non-Goals:**

- Instrumentar la aplicación para contar consultas (`app/core` no se toca).
- `lazy="raise"` global o por relación.
- Refactorizar servicios que ya cumplen, agregar consultas «para llegar a tres» o cargar relaciones que ningún DTO publica.
- Medir el alta (`04` ya lo hizo), `BackgroundTasks` (`06`), contenedor (`07`) y despliegue (`08`).
- Cambiar el orden de los listados: ya se ordenan por clave primaria desde `03`.

## Decisions

### 1. Auditoría de lecturas: ruta → consultas esperadas

Se midieron las trece lecturas contra la base sembrada, cada una en una sesión nueva, contando las sentencias que empiezan con `SELECT` con el evento `before_cursor_execute`. La tabla es el resultado de la auditoría y el contrato que `test/consultas_n1.py` verifica para los dos detalles.

| Ruta | Carga anticipada | `SELECT` esperados | Medido |
|---|---|---|---|
| `GET /editoriales/` | ninguna: `EditorialRead` no publica relaciones | 1 | 1 |
| `GET /editoriales/{id}` | ninguna: `session.get` | 1 | 1 |
| `GET /editoriales/{id}/libros` | resolución de la editorial + `joinedload(Libro.editorial)`, `joinedload(Libro.genero)` | 2 | 2 |
| `GET /generos/` | ninguna: `GeneroRead` no publica relaciones | 1 | 1 |
| `GET /generos/{id}/libros` | resolución del género + las dos `joinedload` | 2 | 2 |
| `GET /autores/{id}` | ninguna: `AutorRead` no publica relaciones | 1 | 1 |
| `GET /autores/{id}/libros` | resolución del autor + `joinedload(LibroAutor.libro)` con editorial y género anidados | 2 | 2 |
| `GET /libros/` | `joinedload(Libro.editorial)`, `joinedload(Libro.genero)` | 1 | 1 |
| `GET /libros/{id}` | las dos `joinedload` + `selectinload(Libro.autorias).joinedload(LibroAutor.autor)` | 2 | 2 (libro 1 y libro 9) |
| `GET /clientes/{id}` | `joinedload(Cliente.perfil)` | 1 | 1 |
| `GET /clientes/{id}/ventas` | resolución del cliente + `select(Venta)` sin opciones | 2 | 2 |
| `GET /ventas/` | ninguna: `VentaResumenRead` no publica relaciones | 1 | 1 |
| `GET /ventas/{id}` | `joinedload(Venta.cliente)` + `selectinload(Venta.renglones).joinedload(RenglonVenta.libro)` | 2 | 2 (ventas 1 y 2) |

Las escrituras quedan fuera del contrato de C-07, pero se auditaron para descartar cargas perezosas posteriores al `commit`: `POST /libros/` hace `INSERT` del libro, `INSERT` de las autorías y las dos consultas de la relectura; `POST /ventas/` hace un `SELECT ... IN` de los libros más las dos consultas de la relectura (los tres `SELECT` que ya fija `test/altas_relaciones.py`); `PATCH /libros/{id}` hace las dos consultas de `obtener_libro` y las dos de `_releer_libro`; `PATCH /clientes/{id}` hace una y una. Ninguna de esas rutas serializa una relación sin cargar.

**Conclusión de la auditoría:** ninguna lectura depende de la carga perezosa y ningún DTO publica una relación que su consulta no cargue. No se modifica ningún servicio ni ningún DTO; el único cambio de código es el orden de las dos colecciones (decisión 3).

**Alternativas descartadas:** agregar `selectinload` a los listados «por las dudas» (sumaría una consulta y cargaría datos que `LibroResumenRead`/`VentaResumenRead` no publican); agregar `joinedload` a `listar_ventas` para el cliente (el DTO de resumen no lo declara).

### 2. El contrato es de dos consultas exactas por detalle, con evidencia

La expectativa intuitiva de «tres consultas» (libro + autorías + autores) no es lo que emite SQLAlchemy. Medido en la versión instalada, el detalle de un libro con una autoría y con dos autorías consume **dos** `SELECT`:

```sql
-- 1) libro con sus relaciones a uno
SELECT libro.id, libro.isbn, libro.titulo, libro.precio, libro.stock,
       libro.editorial_id, libro.genero_id,
       editorial_1.id AS id_1, editorial_1.nombre, editorial_1.pais,
       genero_1.id AS id_2, genero_1.nombre AS nombre_1
FROM libro
LEFT OUTER JOIN editorial AS editorial_1 ON editorial_1.id = libro.editorial_id
LEFT OUTER JOIN genero AS genero_1 ON genero_1.id = libro.genero_id
WHERE libro.id = $1::INTEGER

-- 2) autorías con su autor, en una sola consulta de colección
SELECT libro_autor.libro_id, libro_autor.autor_id, libro_autor.rol, libro_autor.orden,
       autor_1.id, autor_1.nombre, autor_1.nacionalidad
FROM libro_autor
LEFT OUTER JOIN autor AS autor_1 ON autor_1.id = libro_autor.autor_id
WHERE libro_autor.libro_id IN ($1::INTEGER)
```

El `joinedload` anidado dentro de `selectinload` no emite una tercera consulta: SQLAlchemy lo pliega como `LEFT OUTER JOIN` de la consulta de la colección. Lo mismo ocurre en la venta:

```sql
-- 1) venta con su cliente
SELECT venta.id, venta.cliente_id, venta.fecha, venta.total,
       cliente_1.id AS id_1, cliente_1.nombre, cliente_1.email
FROM venta
LEFT OUTER JOIN cliente AS cliente_1 ON cliente_1.id = venta.cliente_id
WHERE venta.id = $1::INTEGER

-- 2) renglones con su libro
SELECT renglon_venta.venta_id, renglon_venta.id, renglon_venta.libro_id,
       renglon_venta.cantidad, renglon_venta.precio_unitario, libro_1.id, ...
FROM renglon_venta
LEFT OUTER JOIN libro AS libro_1 ON libro_1.id = renglon_venta.libro_id
WHERE renglon_venta.venta_id IN ($1::INTEGER)
```

Por eso el contrato verificable es **dos consultas exactas** por detalle con al menos un hijo, y no «tres»: forzar tres obligaría a cargar el autor con `selectinload` (una consulta más para una relación a uno, en contra de la regla `joinedload` que pide la consigna) o a emitir un `SELECT` artificial que no aporta nada y viola «ninguna consulta de más». Se prefiere el número real y documentado.

**Colección vacía.** Con la colección vacía `selectinload` no emite la segunda consulta: el detalle de un libro sin autorías o de una venta sin renglones cuesta una consulta. El requisito lo declara como escenario propio para que nadie lea «dos» como una promesa que se rompe con una lista vacía. La semilla no tiene libros sin autorías; el escenario se cubre por lectura del código y no se fuerza en la prueba, que necesita hijos para medir la invariancia.

**Evidencia complementaria.** La misma medición se repitió con un modelo equivalente en SQLite y el resultado fue idéntico (dos `SELECT` con el `joinedload` plegado), lo que descarta que el comportamiento dependa del dialecto.

**Alternativas descartadas:** `selectinload(Libro.autorias).selectinload(LibroAutor.autor)` para llegar a tres (contradice `joinedload` para a-uno y agrega una consulta); un contador propio que cuente «consultas lógicas» (la consigna habla de consultas en la consola, que son sentencias); aceptar «a lo sumo tres» (no distingue una implementación correcta de una que hace N+1 con un techo).

### 3. El orden se declara en el modelo, no en el loader

En SQLAlchemy 2.1.8 `selectinload(...)` devuelve un `Load` sin `.order_by()`; llamarlo lanza `AttributeError: 'Load' object has no attribute 'order_by'` (verificado en el entorno). El orden estable se declara entonces en el mapeo:

```python
# app/modules/libros/models.py
autorias: list["LibroAutor"] = Relationship(
    back_populates="libro",
    sa_relationship_kwargs={"order_by": "LibroAutor.orden, LibroAutor.autor_id"},
)

# app/modules/ventas/models.py
renglones: list["RenglonVenta"] = Relationship(
    back_populates="venta",
    sa_relationship_kwargs={
        "cascade": "all, delete-orphan",
        "passive_deletes": True,
        "order_by": "RenglonVenta.id",
    },
)
```

- El `order_by` de una relación se aplica también a la consulta de `selectinload`; se comprobó con un modelo equivalente: la segunda sentencia termina en `ORDER BY autoria_prueba.orden, autoria_prueba.autor_id` y la colección llega ordenada aunque se haya insertado en desorden.
- La forma de cadena se resuelve contra el registry de clases en la configuración del mapper. Los modelos se importan juntos con `import_model_modules()` antes de `create_all` y antes de cualquier consulta, así que la resolución nunca depende del orden de importación de un script.
- `orden` no es único en la base (el `CHECK` solo exige `>= 1`), pero `LibroCreate` ya rechaza órdenes repetidos en el alta (`04`). El desempate por `autor_id` cubre el caso de datos cargados por SQL con órdenes iguales y hace el orden total.
- `Venta.renglones` conserva `cascade` y `passive_deletes`: agregar `order_by` no cambia el borrado en cascada ni la inserción de los renglones del alta, que se hace sobre un objeto transitorio.
- El orden no altera el contrato: la consigna no fija el orden de `autores` ni de `renglones`, y con la semilla actual las dos colecciones ya salían ordenadas por casualidad. A partir de este change el orden es una garantía.

**Alternativas descartadas:** ordenar en el servicio con `sorted()` después de cargar (funciona, pero deja el orden fuera del mapeo y no lo garantiza para cualquier lectura futura); ordenar en el DTO (más lejos todavía del origen y repite la regla en dos serializadores); `ORDER BY` manual en la consulta de detalle (no aplica a la consulta de `selectinload`, que es la que trae la colección).

### 4. Se mantiene la estrategia de carga por cardinalidad

No se cambia ninguna opción de carga. La regla queda explícita en la spec: `joinedload` para `editorial`, `genero`, `cliente`, `perfil` y `libro` de un renglón; `selectinload` para `autorias` y `renglones`. Las dos colecciones se cargan con `selectinload` justamente para no multiplicar filas en la consulta principal ni necesitar `unique()`; el `joinedload` anidado dentro de ellas no cambia esa decisión.

**Alternativas descartadas:** `joinedload` sobre una colección (multiplica filas y exige `unique()`); `lazy="selectin"` global en los modelos (carga relaciones que el endpoint no usa y tocaría el change `02`).

### 5. La aplicación no se instrumenta para aprobar el parcial

El conteo es una verificación, no una funcionalidad. `app/core` no gana un contador, un middleware ni un `event.listens_for`; la aplicación no cambia su comportamiento para demostrar C-07. El conteo vive en `test/consultas_n1.py` y usa el evento `before_cursor_execute` sobre el motor de la prueba, el mismo mecanismo que ya usan `test/consultas.py` y `test/altas_relaciones.py`. Para la evidencia manual se usa `SQL_ECHO=true`, que ya expone la configuración `app/core/config.py`.

**Alternativas descartadas:** un contador en `app/core/database.py` (código de producción que solo existe para el examen); un middleware que cuente consultas por petición (no distingue las consultas de la lectura de las de la serialización y agrega superficie).

### 6. Los listados no se tocan

`LibroResumenRead` publica `editorial` y `genero`, y `listar_libros` las carga con dos `joinedload`: una sola consulta. `VentaResumenRead` no publica relaciones y `listar_ventas` no declara opciones: una sola consulta. `GET /clientes/{id}/ventas` y los sublistados cuestan dos porque primero resuelven el recurso de la ruta y después listan; ninguna de esas dos consultas depende de la cantidad de filas.

Agregar `selectinload` a un listado que no publica la colección sumaría una consulta y cargaría datos que nadie serializa, justo lo contrario de lo que C-07 evalúa.

**Alternativas descartadas:** cargar autores en `GET /libros/` (payload más grande y una consulta más); unificar la resolución del padre con el listado en una sola consulta (cambiaría el `404` de la ruta y el contrato del `03`).

### 7. La prueba de carga perezosa es la sesión cerrada

Una relación no cargada en una `AsyncSession` falla al accederse fuera del contexto greenlet (`MissingGreenlet`) o después de cerrar la sesión (`DetachedInstanceError`). Por eso la verificación serializa `LibroRead` y `VentaRead` **después** de cerrar la sesión y el motor: si faltara una relación, la prueba falla en vez de disparar una consulta silenciosa. Además se afirma que el registro de sentencias no creció entre la última lectura y la serialización.

No se usa `lazy="raise"`: rompería las rutas de escritura que devuelven una entidad recién creada sin recargarla (`POST /clientes/`, `POST /editoriales/`, `POST /autores/`, `POST /generos/`, `POST /clientes/{id}/perfil`) y no aporta nada que la sesión cerrada no demuestre.

**Alternativas descartadas:** `lazy="raise"` global (rompe escrituras y no es necesario); `expire_on_commit=True` para forzar la recarga (agrega consultas y puede disparar cargas perezosas); confiar solo en la inspección visual de la consola (no es una prueba).

### 8. `test/consultas_n1.py`: estructura de la medición

El script sigue el estilo de `test/consultas.py` y `test/altas_relaciones.py`: ruta del proyecto en `sys.path`, `import_model_modules()`, `create_async_engine(settings.database_url)`, evento `before_cursor_execute`, `assert` y código de salida distinto de cero si algo falla. No usa `pytest`.

1. Crea con el prefijo `Prueba 05`: un cliente, dos libros (uno con 1 autoría y otro con 5, con ISBN propios y una editorial y un género de la semilla) y dos ventas (una con 1 renglón y otra con 5, con libros distintos de la semilla).
2. Para cada uno de los cuatro casos, abre una sesión nueva, limpia el registro y llama a `obtener_libro`/`obtener_venta`. Afirma que las sentencias `SELECT` son exactamente **2** y guarda el número para comparar 1 contra 5 hijos.
3. Afirma que la segunda sentencia del libro es la de la colección (`FROM libro_autor`) y la de la venta (`FROM renglon_venta`), para que el número no se cumpla por casualidad con dos consultas de otra cosa.
4. Afirma el orden: `[a.orden for a in libro.autorias]` es ascendente y `[r.id for r in venta.renglones]` es ascendente; repite la lectura y compara la secuencia para demostrar que es reproducible.
5. Cierra la sesión y serializa `LibroRead` y `VentaRead` con `model_dump(mode="json")`: no debe lanzar, el registro no debe crecer y las listas serializadas deben salir ordenadas.
6. En `finally`: elimina renglones, ventas, autorías, libros y cliente con `delete()` en orden inverso de dependencias, hace `commit`, cuenta las nueve tablas y afirma `7, 5, 10, 9, 10, 4, 4, 2, 4`; después dispone el motor.

El script exige la base sembrada y sin filas de pruebas anteriores; el docstring lo dice y el orden de ejecución recomendado es después de la limpieza de los `.http`.

**Alternativas descartadas:** crear los datos con `POST` HTTP (mezcla el transporte con la medición y necesita el servidor arriba); contar con `SQL_ECHO` y leer la consola (no es automatizable); medir sobre los datos de la semilla (no hay un libro con cinco autorías ni una venta con cinco renglones).

### 9. Bloques C-07 en `test/lecturas.http`

Se agregan cuatro bloques y una limpieza, sin tocar los existentes:

1. `POST /libros/` con cinco autorías de la semilla, `# captura: libro_c07_id`, `# esperado: 201`.
2. `GET /libros/{{libro_c07_id}}` con `# esperado: 200`, `# contiene:` los cinco nombres y `# cantidad: autores=5`.
3. `POST /ventas/` con cinco renglones sobre cinco libros de la semilla, `# captura: venta_c07_id`, `# esperado: 201`.
4. `GET /ventas/{{venta_c07_id}}` con `# esperado: 200`, `# contiene:` los cinco títulos, `# cantidad: renglones=5` y `# termina-en-z: fecha`.
5. Bloque SQL de limpieza por los dos `id` capturados, al final del archivo.

`# cantidad:` es una directiva nueva de la convención de los `.http`: `# cantidad: campo=n` significa que el arreglo `campo` del cuerpo tiene `n` elementos. No hay un ejecutor en el repositorio —los `.http` se contrastan a mano o con la extensión del editor—, así que la directiva documenta la comprobación con la misma forma que `# contiene:` y `# es-null:`.

El conteo de consultas **no** se mide por HTTP: la evidencia es `test/consultas_n1.py` y el extracto de `SQL_ECHO=true`. Los bloques HTTP demuestran la forma de la respuesta y el orden con varios hijos.

**Alternativas descartadas:** un `.http` nuevo para C-07 (fragmenta la lectura y obliga a otro bloque de limpieza); medir consultas con un cliente HTTP (no hay forma de contar sentencias desde fuera del proceso).

### 10. Contrato HTTP intacto

No cambian rutas, códigos, campos ni serializadores. `LibroRead.autores` sigue siendo la lista de `LibroAutorRead` (`autor`, `rol`, `orden`) y `VentaRead.renglones` la lista de `RenglonRead` (`libro_id`, `titulo`, `cantidad`, `precio_unitario`, `subtotal`). El único cambio observable es el orden estable de las dos listas, que el contrato no fijaba. `test/rutas.py` sigue exigiendo 26 rutas.

### 11. Compatibilidad con Python 3.12

Los cambios son dos argumentos de relación con cadenas y dos archivos de verificación; no introducen sintaxis nueva. Se mantienen las reglas del `03`: `typing.Optional`, `list[...]`, `datetime.timezone.utc`, sin alias `type`, sin genéricos PEP 695, sin `Self`, sin `StrEnum` y sin `datetime.UTC`. El script usa `asyncio.run`, `Path` y `assert`, disponibles en 3.12.

**Alternativas descartadas:** aprovechar características de 3.14 del entorno local (la imagen de entrega es 3.12).

## Risks / Trade-offs

- **El número de consultas depende de la versión de SQLAlchemy.** `requirements.txt` declara `>=2.0` y la medición es de 2.1.8; si una versión futura dejara de plegar el `joinedload` anidado, el detalle pasaría a tres consultas y `test/consultas_n1.py` fallaría. → Es el comportamiento deseado: el número es un contrato y el fallo avisa que hay que revisar la expectativa, no que se rompió la API. Se documenta en el docstring del script.
- **La expectativa intuitiva era de tres consultas.** → Se mide y se documenta la evidencia; forzar tres requeriría una consulta de más o `selectinload` para una relación a uno. Queda anotado en las preguntas abiertas por si la corrección espera el número intuitivo.
- **`order_by` como cadena se resuelve al configurar el mapper.** Un error de tipeo fallaría al importar los modelos, no en una consulta. → Los modelos se importan juntos con `import_model_modules()` y cualquier prueba lo detecta de inmediato; el nombre se verificó contra las clases reales.
- **`orden` repetido en datos cargados por SQL.** → El desempate por `autor_id` hace el orden total; el alta ya rechaza órdenes repetidos.
- **La prueba escribe filas.** → Prefijo `Prueba 05`, limpieza en `finally` y verificación de los nueve conteos de la semilla. Si otra prueba dejó filas, el script falla al final: es una señal de limpieza pendiente, no un falso positivo.
- **`# cantidad:` no tiene ejecutor.** → Se documenta su sintaxis en el encabezado de `test/lecturas.http`; los demás `.http` ya dependen de una lectura manual.
- **El detalle de un libro sin autorías cuesta una consulta.** → Se declara como escenario para que la diferencia no se lea como un incumplimiento; la invariancia que pide C-07 es con uno y con varios hijos.

## Migration Plan

No hay cambios de esquema ni migraciones. Para aplicar y verificar:

1. `docker start pg-libreria` y confirmar los nueve conteos de la semilla.
2. Ejecutar `.venv\Scripts\python.exe test\consultas_n1.py` y comprobar que imprime el conteo de los cuatro casos y termina con `ok`.
3. Ejecutar `uvicorn app.main:app --port 8000` y correr los cinco `.http` de dominio, incluidos los bloques C-07 de `test/lecturas.http`.
4. Ejecutar la regresión: `.venv\Scripts\python.exe test\consultas.py`, `test\altas_relaciones.py`, `test\rutas.py`, `test\serializacion.py` y `test\errores_integridad.py`.
5. Repetir un `GET /libros/{id}` y un `GET /ventas/{id}` con `SQL_ECHO=true` y guardar el extracto de las dos sentencias de cada uno como evidencia de C-07.
6. Ejecutar la limpieza de los `.http` y volver a comprobar `7, 5, 10, 9, 10, 4, 4, 2, 4`.

Rollback: revertir el commit de implementación quita los dos `order_by`, el script y los bloques C-07; los servicios, los DTO y la base no cambian.

## Open Questions

- **Dos contra tres consultas.** La consigna solo pide «cantidad fija, la misma con uno o con varios hijos»; la medición da dos por detalle. Si la corrección espera tres como número literal, la única forma de producirlas sin contradecir «`joinedload` para a-uno» es aceptar una consulta artificial; se prefiere documentar el número real y sostenerlo con la evidencia.
- **Directiva `# cantidad:`.** No existía en la convención de los `.http`; se define acá. Si el grupo prefiere no ampliar la convención, los mismos bloques pueden expresar la cantidad con `# contiene:` repitiendo los cinco elementos.
- **Orden de `renglones` por `id`.** Es el orden de inserción y el que la semilla ya exhibe. Si el negocio pidiera otro criterio (por ejemplo, por `libro_id`), el cambio es una cadena en el modelo y una aserción en el script.
