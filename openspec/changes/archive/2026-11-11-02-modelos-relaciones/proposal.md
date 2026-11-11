# Proposal

## Why

El criterio «Modelos, restricciones y relaciones» (22 % de la nota) exige que el dominio de la librería exista como modelo de tabla con sus restricciones de integridad y su navegación declarada en los dos extremos de cada clave foránea. Hoy los seis `models.py` de dominio son andamiaje vacío: la base creada por el change `01` no tiene ninguna tabla de negocio y los changes `03` a `06` no tienen sobre qué construir contratos, CRUD, altas con relaciones ni lecturas sin N+1.

## What Changes

- Se implementan las nueve tablas del dominio con los nombres obligatorios de tabla y columna: `editorial`, `genero`, `autor`, `libro`, `libro_autor`, `cliente`, `perfil_cliente`, `venta` y `renglon_venta`, distribuidas en los `models.py` de `editoriales`, `generos`, `autores`, `libros`, `clientes` y `ventas`.
- Se declaran las restricciones de integridad en la base, no en Python: `UNIQUE` en `editorial.nombre`, `genero.nombre`, `libro.isbn`, `cliente.email` y `perfil_cliente.cliente_id`; `CHECK` de `precio > 0` y `stock >= 0` en `libro`, `orden >= 1` y `rol IN (...)` en `libro_autor`, `total >= 0` en `venta`, `cantidad > 0` y `precio_unitario > 0` en `renglon_venta`; claves foráneas con índice explícito y borrado en cascada de `renglon_venta` cuando se elimina su `venta`.
- Se declara la navegación en ambos extremos con `Relationship(back_populates=...)`: libro ↔ género (agregación opcional), libro ↔ autoría ↔ autor (muchos a muchos con datos, sin `link_model`), cliente ↔ perfil (uno a uno con `Cliente.perfil` como objeto), venta ↔ cliente y venta ↔ renglón (composición) y renglón ↔ libro.
- El dinero se representa con `Decimal` sobre `NUMERIC(10,2)` y `NUMERIC(12,2)`; ninguna columna monetaria usa `float`. `venta.fecha` se declara con zona horaria.
- Se agrega `scripts/datos_iniciales.py`, ejecutable con el `.venv`, que traduce la semilla del frontend (`libreria_abc/js/datos-iniciales.js`) al modelo nuevo: 7 editoriales, 5 géneros, 10 autores, 9 libros, 4 clientes con 4 perfiles, 2 ventas y 4 renglones. El script advierte si la base ya tiene datos en lugar de duplicarlos.
- Se agregan casos de verificación ejecutables en `test/`: `modelos_esquema.sql` para tablas, columnas, tipos e índices; `modelos_restricciones.sql` para las violaciones de unicidad, `CHECK`, clave foránea y cascada; `modelos_semilla.sql` para los conteos y totales; y `modelos_navegacion.py` para la navegación bidireccional.

No se modifica `app/main.py` ni `app/core/registry.py`: el registro ya importa los seis módulos y `create_all` crea las tablas nuevas al arrancar.

**Fuera de alcance:** DTO en `schemas.py`, CRUD, paginación, códigos `201`/`404`/`409`/`422` (`03`); altas con relaciones (`04`); carga anticipada con `selectinload` (`05`); `BackgroundTasks` (`06`); `Dockerfile` y `.dockerignore` (`07`); `DEPLOY.md` y despliegue (`08`). No se agregan dependencias ni `pytest`: `requirements.txt` no cambia.

## Capabilities

### New Capabilities

- `domain-model`: las nueve tablas del dominio con sus columnas, tipos, claves primarias, ubicación por módulo, representación decimal del dinero y fecha con zona horaria.
- `integrity-constraints`: restricciones que la base hace cumplir por sí misma (unicidad, `CHECK`, claves foráneas, índices y borrado en cascada).
- `entity-relationships`: navegación declarada en los dos extremos de cada relación, con la cardinalidad que fija el modelo de dominio.
- `seed-data`: script de datos iniciales que puebla la base desde la semilla del frontend y no duplica datos existentes.

### Modified Capabilities

- Ninguna. Los requisitos vigentes de `project-structure`, `runtime-lifecycle` y `health-checks` se mantienen: este change agrega contenido a módulos ya previstos y no altera el ciclo de vida ni las sondas de salud.

## Impact

- **Código modificado:** `app/modules/{editoriales,generos,autores,libros,clientes,ventas}/models.py`.
- **Código nuevo:** `scripts/datos_iniciales.py`, `test/modelos_esquema.sql`, `test/modelos_restricciones.sql`, `test/modelos_semilla.sql` y `test/modelos_navegacion.py`.
- **Esquema de base:** nueve tablas nuevas en la base configurada por `DATABASE_URL`; `create_all` las crea al arrancar sin migraciones. Una base existente con tablas del change `01` no se altera.
- **API:** sin cambios; no se agregan rutas ni servicios.
- **Dependencias:** ninguna nueva. `requirements.txt` no se toca.
- **Riesgos:** `create_all` no migra, así que un cambio posterior de estos modelos exige recrear la base en desarrollo; el script de semilla debe advertir de forma visible y no silenciosa cuando la base ya está poblada; la sintaxis debe seguir siendo válida en Python 3.12 aunque el entorno local tenga 3.14.
