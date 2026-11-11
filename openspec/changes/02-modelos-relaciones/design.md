# Design

## Context

Ver `proposal.md` para la motivación y `specs/` para los requisitos. El estado que condiciona el diseño:

- El change `01` dejó el `lifespan` que crea el motor, publica la fábrica de sesiones y ejecuta `SQLModel.metadata.create_all` con los seis `models.py` de dominio ya importados por `app/core/registry.py`. Este change solo agrega clases a esos archivos.
- La base es PostgreSQL 16.15 en el contenedor `pg-libreria`, publicado en `127.0.0.1:5433`; el puerto 5432 lo ocupa un PostgreSQL 18 nativo ajeno al proyecto.
- `create_all` crea tablas faltantes y no modifica las existentes: no hay migraciones en el alcance.
- El entorno local corre Python 3.14, pero la imagen de entrega parte de `python:3.12-alpine`.
- Los modelos de seis módulos se referencian entre sí (libros con editoriales, géneros y autores; ventas con clientes y libros), lo que obliga a resolver imports circulares.
- La semilla del frontend (`libreria_abc/js/datos-iniciales.js`) usa ids de texto, precios con punto flotante y no registra stock, países, nacionalidades, teléfonos ni direcciones.

## Goals / Non-Goals

**Goals:**

- Que el esquema que crea `create_all` al arrancar sea el modelo de dominio completo, con las restricciones viviendo en PostgreSQL y no en validaciones de Python.
- Que la navegación entre entidades funcione en los dos sentidos sin consultas manuales por identificador.
- Que la semilla del frontend quede cargada y sirva como evidencia ejecutable del modelo.

**Non-Goals:**

- DTO, CRUD, rutas de dominio, paginación, códigos de estado y manejo de errores HTTP (`03`).
- Altas con relaciones anidadas (`04`), carga anticipada con `selectinload` (`05`) y tareas en segundo plano (`06`).
- Migraciones de esquema, borrado lógico, auditoría y validación de ISBN con dígito de control.
- Cualquier cambio en `app/main.py`, `app/core/registry.py`, `app/core/database.py` o `requirements.txt`.

## Decisions

### 1. Nombres de tabla explícitos y clases en singular

Cada modelo declara `__tablename__` de forma explícita (`editorial`, `genero`, `autor`, `libro`, `libro_autor`, `cliente`, `perfil_cliente`, `venta`, `renglon_venta`) y una clase en singular (`Editorial`, `Genero`, `Autor`, `Libro`, `LibroAutor`, `Cliente`, `PerfilCliente`, `Venta`, `RenglonVenta`).

Dejar que SQLModel derive el nombre desde la clase produce `perfilcliente`, `libroautor` y `renglonventa`, que no coinciden con los nombres obligatorios. La declaración explícita elimina esa dependencia de la heurística.

**Alternativas descartadas:** confiar en el nombre derivado (falla en las tres tablas compuestas); usar `table=True` con nombres en plural (contradice la consigna).

### 2. Importes con `sa_column` y `Numeric`, nunca `float`

```python
precio: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
```

La versión instalada de SQLModel (0.0.49) también traduce `Field(max_digits=10, decimal_places=2)` a `NUMERIC(10,2)`, pero `requirements.txt` declara `sqlmodel>=0.0.24` sin techo de versión: con `sa_column` el tipo exacto queda escrito en el modelo y no depende de cómo la versión resuelta interprete los parámetros. Además, `sa_column` es el mismo mecanismo que exige `DateTime(timezone=True)` y deja `nullable` junto al tipo. Los `CHECK` de rango se declaran aparte, en `__table_args__`.

**Alternativas descartadas:** `float` (prohibido por la consigna y fuente de errores de redondeo en importes); `Numeric` sin precisión (acepta valores fuera del rango esperado); validar el rango solo en Python (no protege escrituras directas a la base).

### 3. Restricciones `CHECK` nombradas en `__table_args__`

Cada regla de rango o de dominio se declara con nombre estable:

```python
__table_args__ = (
    CheckConstraint("precio > 0", name="ck_libro_precio_positivo"),
    CheckConstraint("stock >= 0", name="ck_libro_stock_no_negativo"),
)
```

Nombrarlas permite verificarlas en `pg_constraint` y en `\d <tabla>`, y hace legible el error de PostgreSQL. Las reglas cubiertas son las de `libro` (`precio > 0`, `stock >= 0`), `libro_autor` (`orden >= 1`, `rol IN ('autor','coautor','traductor','ilustrador')`), `venta` (`total >= 0`) y `renglon_venta` (`cantidad > 0`, `precio_unitario > 0`).

**Alternativas descartadas:** validar en `field_validator` (el enunciado pide restricciones de tabla y la validación se saltea con SQL directo); `Enum` de PostgreSQL para `rol` (el enunciado pide un `CHECK` y un `Enum` agrega un tipo que `create_all` debe crear antes).

### 4. Índices: explícitos donde la base no los crea

PostgreSQL indexa claves primarias y columnas `UNIQUE`, pero no claves foráneas. El reparto queda así:

| Columna | Cobertura |
|---|---|
| `libro.editorial_id`, `libro.genero_id` | `index=True` en el campo |
| `libro_autor.libro_id` | columna líder de la clave primaria compuesta |
| `libro_autor.autor_id` | `index=True` explícito |
| `perfil_cliente.cliente_id` | índice único de la restricción `UNIQUE` |
| `venta.cliente_id` | `index=True` |
| `renglon_venta.venta_id`, `renglon_venta.libro_id` | `index=True` |

No se agrega un índice simple sobre una columna ya cubierta por la clave primaria o por una restricción de unicidad: sería redundante y duplicaría el costo de escritura.

**Alternativas descartadas:** `Index` compuesto sobre `(venta_id, libro_id)` (no cubre las búsquedas por `libro_id` por separado y el enunciado pide índice por clave foránea); índice único en `libro_autor` sobre `(libro_id, orden)` (agregaría una regla que la consigna no pide).

### 5. Unicidad donde la consigna la exige

- `editorial.nombre`, `genero.nombre`, `libro.isbn`, `cliente.email`: `unique=True` en el campo.
- `perfil_cliente.cliente_id`: `unique=True`, que es lo que convierte la relación en uno a uno a nivel de base.

La unicidad no se replica con una consulta previa en la aplicación: la base es la que rechaza el duplicado, y el `409` que traduzca ese error llegará en `03`.

**Alternativas descartadas:** `Index(unique=True)` separado del campo (equivalente, pero dispersa la definición); validar con un `SELECT` antes de insertar (sujeto a carreras entre peticiones concurrentes).

### 6. Autorías como entidad con clase propia, sin `link_model`

`LibroAutor` es una tabla con clase, clave primaria compuesta `(libro_id, autor_id)` y sus propios atributos `rol` y `orden`. La navegación queda:

```
Libro.autorias  ->  list[LibroAutor]  ->  .autor  ->  Autor
Autor.autorias  ->  list[LibroAutor]  ->  .libro  ->  Libro
```

`link_model` de SQLModel genera una tabla de enlace sin atributos accesibles, que escondería `rol` y `orden`; por eso se descarta. El precio de esta decisión es que no existe una colección directa `libro.autores`: se navega `libro.autorias[i].autor`, tal como pide la consigna.

**Alternativas descartadas:** `link_model` (pierde los datos de la relación); dos tablas, una de enlace y otra de detalle (duplica la clave y permite inconsistencias).

### 7. Uno a uno explícito con `uselist: False`

```python
perfil: Optional["PerfilCliente"] = Relationship(
    back_populates="cliente",
    sa_relationship_kwargs={"uselist": False},
)
```

SQLAlchemy deduce uno a muchos desde el lado del cliente porque la clave foránea vive en `perfil_cliente`. Sin `uselist: False` el atributo sería una lista, que es exactamente lo que la consigna prohíbe. La unicidad de `perfil_cliente.cliente_id` sostiene la cardinalidad en la base; `uselist: False` la refleja en el modelo.

**Alternativas descartadas:** `Relationship(..., uselist=False)` pasado como argumento directo (SQLModel no lo expone; va por `sa_relationship_kwargs`); dejarlo como colección y tomar el primer elemento en el servicio (contradice el enunciado).

### 8. Composición con cascada en la base y en la sesión

`renglon_venta.venta_id` declara `ondelete="CASCADE"` y `Venta.renglones` declara `cascade="all, delete-orphan"` con `passive_deletes=True`.

La cascada en la clave foránea es la que actúa cuando el borrado se hace con SQL directo o desde otra conexión; la cascada de la relación es la que ordena el grafo cuando se borra desde la sesión. `passive_deletes=True` evita que SQLAlchemy cargue los renglones solo para borrarlos, porque la base ya lo hace.

**Alternativas descartadas:** solo cascada de ORM (un `DELETE` directo en SQL dejaría renglones huérfanos y fallaría por clave foránea); solo `ondelete` sin cascada de ORM (el objeto en memoria quedaría con renglones inexistentes).

### 9. Referencias entre módulos con `TYPE_CHECKING` y anotaciones en texto

Los modelos se referencian entre archivos (`Libro` con `Editorial`, `Genero` y `LibroAutor`; `Venta` con `Cliente`, `RenglonVenta` y `Libro`). Para no crear imports circulares:

- Cada módulo importa sus dependencias solo bajo `if TYPE_CHECKING:`.
- Las anotaciones de relación van como texto (`list["Libro"]`, `Optional["Genero"]`), usando `typing.Optional` en lugar de `X | None` dentro de la cadena.
- No se usa `from __future__ import annotations` en los modelos: las anotaciones de relación se evalúan al configurar los mapeos y conviene que lo hagan igual en el entorno local y en la imagen 3.12.
- El registro (`import_model_modules()`) importa los seis módulos antes de `create_all`, así que todas las clases existen cuando SQLAlchemy configura los mapeos. Cualquier script que use los modelos debe llamar primero a `import_model_modules()`.

**Alternativas descartadas:** imports directos entre módulos (ciclo de importación al arrancar); un único archivo `models.py` global (rompe la estructura obligatoria por módulo); resolver las relaciones por nombre de tabla sin clase (impide navegar).

### 10. Nulos en los datos que la semilla no trae

La semilla no registra `editorial.pais`, `autor.nacionalidad`, `perfil_cliente.telefono` ni `perfil_cliente.direccion`. Esas columnas se declaran opcionales y la carga las deja en `NULL`, en lugar de inventar datos que después habría que corregir. `libro.genero_id` es opcional por el modelo de dominio y la semilla ya trae un libro sin género (`Veinte poemas de amor`).

`libro.stock` es obligatorio y la semilla no lo trae: el script asigna `10` a cada libro, como valor explícito y documentado en el propio script. Se prefiere un valor explícito a un `default` en el modelo, para que ninguna escritura futura herede un stock que nadie decidió.

**Alternativas descartadas:** `server_default` en `stock` (oculta la decisión en el esquema y complica la lectura del modelo); deducir países y nacionalidades por autor (datos inventados que la consigna no pide); dejar `stock` nulo (viola el `CHECK` y el modelo de dominio).

### 11. Script de datos iniciales en este change, no en `03`

El script vive en `scripts/datos_iniciales.py` y se justifica acá por cuatro razones:

1. Es la única forma de comprobar el modelo completo con datos reales: las nueve tablas, las restricciones y las relaciones se ejercitan con la semilla, que es el caso de uso del parcial.
2. La semilla es la fuente del dominio. Si el script se posterga, el modelo se diseña sin confrontar contra los datos que va a recibir y las diferencias (ids de texto, importes con decimales, autorías múltiples) aparecen recién en `04`.
3. `03` es el change de contratos y CRUD: su superficie es HTTP. El script es una herramienta de línea de comandos para desarrollo y demostración, no un endpoint, y no debe confundirse con el CRUD.
4. `04` (altas con relaciones) y `05` (lecturas sin N+1) necesitan una base poblada para demostrarse. Tenerla desde `02` evita que cada change invente su propia carga.

El script no crea una dependencia nueva: usa el motor asincrónico, la configuración y los modelos que ya existen. Es autocontenido en el sentido de que ejecuta `create_all` antes de insertar, así que puede correr sin que la aplicación se haya arrancado nunca.

**Alternativas descartadas:** cargar la semilla con `INSERT` en un `.sql` (duplicaría los ids de texto a mano y no valida el modelo a través de las clases); sembrar en `03` junto al CRUD (mezcla herramientas de desarrollo con la superficie HTTP); sembrar desde el `lifespan` (datos de demo en producción).

### 12. Traducción de la semilla

| Origen (`datos-iniciales.js`) | Destino |
|---|---|
| ids de texto (`"ed-sudamericana"`, `"li-hobbit"`) | ids `int` generados por la base; el script arma un mapa `nombre`/`isbn`/`email` → `id` después de cada `flush` |
| `precio: 24500.0` | `Decimal("24500.00")` |
| `generoId: null` | `libro.genero_id = NULL` |
| `autorIds: [...]` | filas de `libro_autor` con `rol` `autor`/`coautor` y `orden` desde `1` |
| clientes sin perfil | un `perfil_cliente` por cliente, con `telefono` y `direccion` en `NULL` |
| `fecha: "2026-03-14"` | `datetime(2026, 3, 14, 0, 0, tzinfo=timezone(timedelta(hours=-3)))` |
| `precioUnitario` del renglón | copia del `precio` del libro al momento de la carga |
| `total` de la venta | se recalcula como suma de `cantidad * precio_unitario` y se contrasta con el total de la semilla |

El script trabaja en una sola transacción: verifica que las nueve tablas estén vacías, inserta todo, contrasta totales y hace un único `commit`. Si algo falla, hace `rollback` y no deja datos parciales. Si encuentra filas en cualquier tabla de dominio, imprime una advertencia, no escribe y termina con código `0`: una segunda ejecución es un no-op informado, no un error.

**Alternativas descartadas:** ids fijos `1..N` (chocan con las secuencias si la base ya se usó); `TRUNCATE` automático para poder repetir (borra datos ajenos sin preguntar); commit por entidad (deja estados parciales si falla a mitad de camino).

### 13. Verificación con archivos ejecutables, sin `pytest`

`requirements.txt` no se toca, así que la verificación se hace con herramientas ya disponibles:

- `test/modelos_esquema.sql`: consultas de solo lectura a `information_schema.columns`, `pg_constraint` y `pg_indexes`, con el resultado esperado en comentarios. Se ejecuta con `psql` dentro del contenedor.
- `test/modelos_restricciones.sql`: un caso de violación por transacción (`BEGIN; INSERT ...; ROLLBACK;`), cada uno con el `SQLSTATE` esperado en un comentario (`23505` unicidad, `23514` CHECK, `23503` clave foránea).
- `test/modelos_navegacion.py`: script asincrónico que abre una sesión, recorre las relaciones en los dos sentidos y afirma que `Cliente.perfil` es un objeto y no una lista. Imprime `ok` y termina con código `0`.
- `test/modelos_semilla.sql`: conteos por tabla, suma de renglones contra `venta.total`, y verificación de que los precios unitarios no dependen del precio actual del libro.

**Alternativas descartadas:** agregar `pytest` (dependencia nueva y fuera del stack de la consigna); un `.http` (no hay endpoints nuevos en este change).

## Risks / Trade-offs

- **`create_all` no migra:** si un modelo cambia después de creado, la base no se actualiza. → En desarrollo se recrea el esquema (`DROP TABLE ... CASCADE` en orden inverso de dependencias); la limitación se documenta en `DEPLOY.md` (`08`).
- **Referencias por texto entre módulos:** un script que importe un solo `models.py` y consulte relaciones falla al configurar los mapeos. → Todos los puntos de entrada (aplicación y scripts) llaman a `import_model_modules()` antes de usar los modelos; queda indicado en el docstring de cada `models.py`.
- **`uselist: False` depende de la unicidad:** si alguien quita el `UNIQUE` de `perfil_cliente.cliente_id`, el modelo seguiría diciendo "uno" y la base permitiría varios. → La unicidad se verifica en `test/modelos_esquema.sql`, no solo en el modelo.
- **Datos inventados en la semilla:** `stock = 10` y los perfiles sin contacto no vienen del frontend. → Están centralizados y comentados en `scripts/datos_iniciales.py`; si aparecen datos reales, se cambian ahí sin tocar el modelo ni las specs.
- **Cascada con `passive_deletes=True`:** los renglones borrados por la base pueden quedar en la identidad de la sesión. → El borrado de ventas se hará en una sesión nueva en `03`; la verificación de este change se hace por SQL.
- **Python local 3.14 vs. imagen 3.12:** una construcción válida en local podría no serlo en la imagen. → Solo se usan características de 3.12 (`list[...]`, `typing.Optional`, sin PEP 695 ni alias `type`); la comprobación definitiva se repite en `07` dentro de `python:3.12-alpine`.
- **Base de desarrollo compartida:** el contenedor es el mismo que usa el resto de los changes y el puerto 5433 no es el estándar. → Las verificaciones usan `DATABASE_URL` del `.env` y nunca hardcodean host ni puerto.

## Migration Plan

No hay datos productivos. Para aplicar y verificar:

1. Arrancar el contenedor `pg-libreria` y confirmar que `DATABASE_URL` apunta a `127.0.0.1:5433`.
2. Si la base tiene tablas de dominio de una prueba anterior, recrearlas: `DROP TABLE IF EXISTS renglon_venta, venta, perfil_cliente, cliente, libro_autor, libro, autor, genero, editorial CASCADE;`.
3. Arrancar la aplicación (o ejecutar el script de datos iniciales, que también ejecuta `create_all`) para crear las nueve tablas.
4. Ejecutar `scripts/datos_iniciales.py` y después los archivos de `test/`.

Rollback: revertir el commit de implementación deja los `models.py` como andamiaje; para limpiar la base alcanza con el `DROP TABLE` del paso 2. No hay migraciones que deshacer.

## Open Questions

- Los valores de `stock` y los datos de contacto de los perfiles son inventados. Si el grupo consigue datos reales del catálogo, se actualizan en el script sin cambiar el modelo ni las specs.
- El formato definitivo de la fecha de venta en la API (`date` o `datetime` con desplazamiento) se decide en `03`, cuando exista el contrato; el modelo ya admite el instante con zona horaria.
