# Proposal

## Why

El criterio «Contratos y CRUD» (12 % de la nota) exige endpoints con DTO separados de los modelos de tabla, códigos HTTP correctos, `PATCH` parcial, listados paginados y búsqueda con parámetros ligados. Hoy los `schemas.py`, `service.py` y `router.py` de los seis módulos de dominio son andamiaje vacío y `app/main.py` solo registra el router de salud: no existe ninguna ruta de negocio. Sin este change, `04` no tiene contratos sobre los que agregar altas con relaciones y `05` no tiene lecturas que optimizar.

## What Changes

- Se implementan los DTO de `schemas.py` para las entidades del modelo: `Create` sin `id`, `Update` con todos los campos opcionales y `Read` con `id`. Los DTO de alta y de actualización rechazan campos desconocidos (`extra="forbid"`), de modo que un `id` en un alta o un campo ajeno al contrato produce `422`.
- Se implementan los endpoints de referencia de la consigna para `editoriales`, `generos`, `autores`, `libros`, `clientes` y `ventas`: altas, lecturas por identificador, `PATCH` parcial, sublistados de libros y ventas y el alta de perfil de un cliente.
- Se implementa el `PATCH` parcial con `exclude_unset`: sólo se escriben los campos enviados y un cuerpo vacío no modifica la fila ni falla.
- Se implementa la paginación obligatoria de RN-10 con una dependencia reutilizable (`limit` 1–100, por defecto 20; `offset` desde 0, por defecto 0) aplicada a **todos** los listados, incluidos `/generos/` y los cuatro sublistados.
- Se implementa la búsqueda de libros por parte del título, sin distinguir mayúsculas, con `ilike` y parámetro ligado, más el filtro opcional `genero_id` (RN-11).
- Se implementa el manejo de errores con excepciones de dominio y traducción centralizada de `IntegrityError`: `404` para recurso inexistente, `409` cuando la base rechaza la escritura (unicidad, clave foránea o `CHECK`) y `422` cuando el cuerpo o los parámetros no cumplen el contrato. Ningún error devuelve nombres de tablas, restricciones, `SQLSTATE` ni trazas (RN-12).
- La unicidad de RN-01, RN-02 y RN-09 se resuelve escribiendo y traduciendo el rechazo de la base, sin consultar antes si el valor existe.
- Las lecturas que devuelven relaciones usan carga anticipada (`joinedload` para a-uno y `selectinload` para colecciones), de modo que `GET /libros/{id}` y `GET /ventas/{id}` no dependen de carga perezosa.
- Se registran los seis routers de dominio en `app/main.py`, junto al de salud, y se agregan archivos `.http` en `test/` con la respuesta esperada de cada caso.

**Fuera de alcance:** `POST /libros/` y `POST /ventas/`, con los DTO `LibroCreate`, `VentaCreate` y `RenglonCreate` (change `04`); la verificación de cantidad fija de consultas (change `05`); `BackgroundTasks` (change `06`); `Dockerfile`, `.dockerignore` y `DEPLOY.md` (changes `07` y `08`). No se agregan dependencias, no se toca `requirements.txt` y no se usa `pytest`.

## Capabilities

### New Capabilities

- `api-contracts`: DTO separados de los modelos de tabla, altas sin `id`, actualizaciones parciales, lecturas con `id` y la forma serializada de importes, fechas y enteros.
- `crud-endpoints`: rutas, métodos, códigos `201`/`404`/`409`/`422`, separación entre router, servicio y contrato, y registro de los routers de dominio.
- `pagination-and-filtering`: paginación obligatoria de todo listado (RN-10) y búsqueda de libros por título con parámetro ligado y filtro por género (RN-11).
- `error-handling`: traducción de los errores de la base a mensajes propios, unicidad garantizada por la base sin consulta previa y ausencia de texto interno en las respuestas (RN-12).

### Modified Capabilities

- Ninguna. Las specs vigentes de `domain-model`, `entity-relationships`, `integrity-constraints`, `seed-data`, `project-structure`, `runtime-lifecycle` y `health-checks` se mantienen: este change agrega la capa HTTP sobre el modelo existente y no cambia tablas, restricciones, relaciones ni ciclo de vida.

## Impact

- **Código modificado:** `app/main.py` (registro de los seis routers), `app/modules/{editoriales,generos,autores,libros,clientes,ventas}/schemas.py`, `service.py` y `router.py`.
- **Código nuevo:** `app/core/pagination.py`, `app/core/errors.py`, `test/contratos.http`, `test/paginacion.http`, `test/errores.http`, `test/lecturas.http` y los scripts de verificación que no son HTTP.
- **API:** se agregan las rutas de la tabla de endpoints de referencia. `GET /health/live` y `GET /health/ready` no cambian.
- **Base de datos:** sin cambios de esquema. Las escrituras usan la base sembrada por `02` y las restricciones que ya existen.
- **Dependencias:** ninguna nueva. `requirements.txt` no se toca.
- **Riesgos:** el `409` depende de traducir el `IntegrityError` sin filtrar su texto; la paginación de `/generos/` y de los sublistados excede la tabla de endpoints pero la exige RN-10; el `PATCH` debe distinguir «campo ausente» de «campo con valor nulo» en `libro.genero_id`.
