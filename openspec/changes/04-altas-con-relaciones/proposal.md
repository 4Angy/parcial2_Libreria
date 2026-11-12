# Proposal

## Why

El criterio «Altas con relaciones: ids y datos» (17 % de la nota) exige las dos altas que el change `03` dejó deliberadamente fuera: `POST /libros/` con la lista de autorías y `POST /ventas/` con la lista de renglones. Hoy el catálogo solo se puede poblar por SQL, no se puede demostrar RN-04 a RN-07 ni los casos C-04, C-05 y C-06, y el change `05` no tiene un alta de venta sobre la que medir consultas. Este change cierra ese hueco sin tocar las lecturas, la paginación ni los contratos ya publicados.

## What Changes

- Se agregan `LibroCreate` y `LibroAutorCreate` en `app/modules/libros/schemas.py`: el alta recibe los ids de editorial, género y autores, más `rol` y `orden` de cada autoría. Ningún campo `id` viaja en el cuerpo y un campo extra responde `422`.
- Se agrega `POST /libros/` con respuesta `201` y el detalle `LibroRead` (editorial, género y autores con `rol` y `orden`). El alta escribe el libro y sus autorías en una transacción y traduce el ISBN repetido a `409`.
- Se agregan `VentaCreate` y `RenglonCreate` en `app/modules/ventas/schemas.py`: el alta recibe `cliente_id` y los renglones con `libro_id` y `cantidad`. No viajan `id`, `precio_unitario`, `subtotal`, `total` ni `fecha`.
- Se agrega `POST /ventas/` con respuesta `201` y `VentaRead` con cliente y renglones. La venta nace con sus renglones, el servidor copia el precio de cada libro y calcula el total (RN-04, RN-06 y RN-07); la fecha la pone el servidor.
- Se valida en el DTO, con `422`, que una venta tenga al menos un renglón y que un mismo libro no se repita (RN-05); se rechaza también un `autor_id` repetido y un `orden` repetido en la misma alta de libro.
- Las referencias inexistentes se resuelven escribiendo: la clave foránea de `editorial_id`, `genero_id`, `autor_id` y `cliente_id` se traduce a `409` con un mensaje propio y sin consultar antes si el id existe (C-04 y C-05, RN-12). La única lectura previa es la de los libros de una venta, necesaria para copiar el precio.
- Se actualizan las verificaciones existentes: `test/rutas.py` pasa a exigir las dos altas (y sigue exigiendo que no haya `PATCH /ventas/{id}` ni `PUT`/`DELETE`), y `test/contratos.http` y `test/errores.http` reemplazan los bloques que esperaban `405` por los casos reales de alta y por C-04 y C-05.

**Fuera de alcance:** `PATCH /ventas/{id}` (RN-08, sigue respondiendo `405`); la medición formal y documentada del número de consultas (change `05`); `BackgroundTasks` (change `06`); `Dockerfile`, `.dockerignore` y `DEPLOY.md` (changes `07` y `08`); cualquier cambio de tablas, restricciones o migraciones. No se agregan dependencias, no se toca `requirements.txt`, no se usa `pytest` y no se modifica `scripts/datos_iniciales.py`.

## Capabilities

### New Capabilities

- `nested-write-contracts`: contratos de alta con DTO anidados (`LibroCreate` con `autores`, `VentaCreate` con `renglones`), campos que no viajan en el cuerpo, `extra="forbid"` y las validaciones de RN-04 y RN-05 que responden `422` antes de llegar a la base.
- `sale-registration`: alta transaccional de la venta con sus renglones, copia del precio del libro (RN-06), cálculo del total por el servidor (RN-07), fecha del servidor, respuesta con cliente y renglones y alta de libro con autorías en la misma transacción.

### Modified Capabilities

- `crud-endpoints`: los requisitos «Rutas de libros» y «Rutas de ventas sin modificación» hoy prohíben `POST /libros/` y `POST /ventas/`; el delta los reemplaza para publicar ambas altas y mantener la ausencia de `PATCH /ventas/{id}`.
- `error-handling`: se agrega el rechazo de referencias inexistentes en las altas, con `409` y mensaje propio, sin consulta previa de existencia (RN-12, C-04 y C-05).

## Impact

- **Código modificado:** `app/modules/libros/schemas.py`, `service.py` y `router.py`; `app/modules/ventas/schemas.py`, `service.py` y `router.py`. `app/main.py` no cambia porque los dos routers ya están registrados.
- **Código nuevo:** `test/altas.http` (casos de alta con relaciones), `test/altas_relaciones.py` (verificación ejecutable de RN-06, RN-07 y del número fijo de consultas) y la ampliación de `test/serializacion.py`.
- **API:** se agregan `POST /libros/` y `POST /ventas/` con `201`, `409` y `422`. Las rutas del `03` conservan su contrato.
- **Base de datos:** sin cambios de esquema. Se reutilizan las restricciones y las claves foráneas creadas por `02`.
- **Dependencias:** ninguna nueva.
- **Riesgos:** el `409` por clave foránea depende de reutilizar `confirmar()` sin filtrar el texto de la base; el precio copiado debe releerse del libro y no del cuerpo; la respuesta del alta debe evitar la carga perezosa después del `commit`.
