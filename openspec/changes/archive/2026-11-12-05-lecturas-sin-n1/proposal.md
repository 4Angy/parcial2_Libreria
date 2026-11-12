# Proposal

## Why

La consigna del parcial (Ejercicio 5, 8 %) exige que toda respuesta que incluya datos de una relación los obtenga con carga anticipada declarada en la misma consulta (`joinedload` para relaciones a uno y `selectinload` para colecciones), con un número fijo de consultas que no crezca con la cantidad de autores o renglones, y sin depender de la carga perezosa. Hoy esa propiedad se cumple en el código (servicios de libros, ventas, autores, editoriales, géneros y clientes), pero no está capturada como contrato verificable en ninguna spec: no hay un criterio explícito de cantidad de consultas ni de estrategia de carga, y el roadmap (`docs/ESTADO.md`) marca el change `05-lecturas-sin-n1` como fuera de alcance. Formalizarlo cierra la brecha entre el comportamiento real y la especificación, y deja el Ejercicio 5 auditable y archivable.

## What Changes

- Se introduce la capability `eager-loading`, que fija el contrato de carga anticipada para las lecturas que serializan relaciones: estrategia por tipo de relación (`joinedload` para a-uno, `selectinload` para colecciones), número fijo de consultas independiente de la cardinalidad, y prohibición de la carga perezosa.
- Se documenta, para el detalle de libro y el detalle de venta, las relaciones que deben estar materializadas y el límite de consultas.
- Se extiende el mismo contrato a los sublistados y lecturas que incluyen relaciones (autores, editoriales, géneros, clientes) para que ninguna lectura dependa de la carga perezosa.
- Se agregan verificaciones de cantidad de consultas y de serialización fuera de sesión, en línea con `test/consultas.py` y `test/altas_relaciones.py`, como criterio de aceptación del change.
- No se modifican contratos HTTP ni modelos de tabla; es un change de comportamiento de lectura y de especificación.

## Capabilities

### New Capabilities

- `eager-loading`: contrato de carga anticipada para las lecturas que serializan relaciones del dominio, con estrategia por tipo de relación, número fijo de consultas y prohibición de carga perezosa.

### Modified Capabilities

- (ninguna) — las specs existentes (`crud-endpoints`, `entity-relationships`) no cambian sus requisitos; este change agrega una dimensión nueva (estrategia de carga) sin alterar la superficie HTTP ni el modelo de navegación.

## Impact

- Código afectado: `app/modules/libros/service.py` (`_consulta_libro`, `listar_libros`), `app/modules/ventas/service.py` (`_consulta_venta`, `listar_ventas`), `app/modules/autores/service.py`, `app/modules/editoriales/service.py`, `app/modules/generos/service.py`, `app/modules/clientes/service.py`.
- Tests afectados: `test/consultas.py`, `test/altas_relaciones.py` y un nuevo caso de verificación de cantidad de consultas para el detalle de libro y de venta.
- Sin cambios en `openspec/specs/` existentes ni en el esquema de la base; el change agrega una spec nueva (`specs/eager-loading/spec.md`) que al archivarse creará `openspec/specs/eager-loading/spec.md`.
- Sin cambios en Docker, despliegue ni entorno.
