# Proposal

## Why

El criterio «Lecturas sin N+1» (8 % de la nota, caso C-07) exige que toda respuesta con datos de una relación los obtenga con carga anticipada declarada en la misma consulta y que el detalle de un libro y el de una venta consuman un número fijo de consultas, el mismo con uno o con varios autores o renglones. La carga anticipada ya está implementada desde los changes `03` y `04`, pero hoy no hay un requisito que la fije como criterio verificable, ni una medición que demuestre que el número no crece con la cantidad de hijos, ni un orden estable de las colecciones que haga la respuesta reproducible. Sin este change, C-07 depende de una inspección manual de la consola y el orden de `autores` y `renglones` queda librado al plan de ejecución de PostgreSQL.

## What Changes

- Se declara la capability `eager-loading`: `joinedload` para relaciones a uno, `selectinload` para colecciones, número fijo de consultas en los dos detalles, serialización sin sesión y orden estable de las colecciones.
- Se agrega `order_by` a la relación `Libro.autorias` (`orden, autor_id`) y a `Venta.renglones` (`id`) mediante `sa_relationship_kwargs`, conservando la cascada y `passive_deletes` de la venta. El orden se declara en el modelo porque en SQLAlchemy 2.1.8 `selectinload(...)` no expone `.order_by()` (verificado: `AttributeError`).
- Se auditan las lecturas existentes contra la base real y se documenta la tabla ruta → consultas esperadas. Si una lectura dependiera de la carga perezosa se corrige con `joinedload`/`selectinload`; la auditoría no encontró ninguna, así que no se refactoriza ningún servicio.
- Se agrega `test/consultas_n1.py`: mide con el evento `before_cursor_execute` el detalle de un libro con 1 y con 5 autores y el de una venta con 1 y con 5 renglones, exige el mismo número fijo en los dos casos, serializa `LibroRead`/`VentaRead` con la sesión cerrada y comprueba el orden de las colecciones.
- Se agregan bloques C-07 en `test/lecturas.http` que muestran la forma de la respuesta del detalle con varios autores y con varios renglones, con limpieza por el `id` capturado.
- Se documenta el extracto de `SQL_ECHO=true` de C-07 como evidencia para `docs/ESTADO.md`.

**Fuera de alcance:** cambios de rutas, DTO, routers, `app/main.py`, `lifespan`, semilla, `Dockerfile`, `requirements.txt` o `pytest`; instrumentación de la aplicación para contar consultas (`app/core` no cambia); `lazy="raise"` global; `BackgroundTasks` (change `06`) y contenedor (change `07`).

## Capabilities

### New Capabilities

- `eager-loading`: obligación de declarar la carga anticipada en la consulta de cada lectura (`joinedload` para a-uno, `selectinload` para colecciones), número fijo y verificable de consultas en el detalle de libro y de venta, serialización correcta con la sesión cerrada, DTO de resumen sin relaciones no cargadas y orden estable de `autores` y `renglones`.

### Modified Capabilities

Ninguna. El orden estable y el conteo fijo son requisitos nuevos que no contradicen `entity-relationships` (no fija orden de colecciones), `crud-endpoints` (no fija el número de consultas) ni `sale-registration` (no fija el orden de los renglones leídos). Si durante la implementación apareciera una contradicción real, se documentará y se propondrá el delta mínimo.

## Impact

- **Código modificado:** `app/modules/libros/models.py` (una opción `order_by` en `Libro.autorias`) y `app/modules/ventas/models.py` (una opción `order_by` en `Venta.renglones`, conservando `cascade` y `passive_deletes`).
- **Código nuevo:** `test/consultas_n1.py`; bloques C-07 en `test/lecturas.http`.
- **API:** mismos cuerpos, códigos y campos. El único cambio observable es que `autores` y `renglones` salen ordenados de forma estable; el contrato no fijaba ese orden.
- **Base de datos:** sin cambios de esquema, restricciones ni datos. Las pruebas crean filas `Prueba 05` y las eliminan al final.
- **Dependencias:** ninguna nueva. La medición usa el evento de SQLAlchemy, disponible en la versión instalada.
- **Riesgos:** que el conteo real no coincida con el esperado (se mide y se documenta antes de fijarlo); que `order_by` declarado como cadena no resuelva contra el registry (los modelos ya se importan juntos con `import_model_modules()`); que una prueba que escribe deje filas o cambie la semilla (limpieza en `finally` y verificación de los nueve conteos).
