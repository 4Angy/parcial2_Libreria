# Design

## Context

El dominio ya declara la carga anticipada en los servicios de libros, ventas, autores, editoriales, géneros y clientes (ver `app/modules/*/service.py`). La base real y los tests (`test/consultas.py`, `test/altas_relaciones.py`) ya verifican serialización fuera de sesión y cantidad fija de consultas para el alta de venta. Falta capturar ese comportamiento como contrato y fijar los criterios de verificación para las lecturas de detalle. Ver `proposal.md` — Why.

## Goals / Non-Goals

**Goals:**

- Fijar, por capability, la estrategia de carga por tipo de relación (`joinedload` para a-uno, `selectinload` para colecciones) y el límite de consultas.
- Garantizar que la serialización de `LibroRead` y `VentaRead` no emita consultas adicionales ni dependa de la carga perezosa.
- Extender el mismo criterio a los sublistados que incluyen relaciones.
- Proveer una verificación automatizada de cantidad de consultas comparable a la del alta de venta.

**Non-Goals:**

- No cambiar contratos HTTP, modelos de tabla ni el esquema de la base.
- No introducir caché, paginación nueva ni índices adicionales.
- No modificar el comportamiento del alta de libros ni de ventas (ya cubierto por `04-altas-con-relaciones`).
- No implementar el Ejercicio 6 (asincronía/background) ni los ejercicios 7 y 8 (contenedor/despliegue).

## Decisions

- **D1 — Estrategia de carga por tipo de relación.** Las relaciones a uno (`editorial`, `genero`, `cliente`, `autor` sobre autoría, `libro` sobre renglón) se cargan con `joinedload` (un `JOIN` en la misma consulta); las colecciones (`autorias`, `renglones`) con `selectinload` (una consulta `SELECT IN` adicional). Alternativa considerada: `joinedload` para todo, que genera `CROSS JOIN` y multiplicación de filas en colecciones; se descarta por el costo de memoria y por la recomendación de la consigna (sección 4.6).
- **D2 — Consulta base reutilizable.** Cada módulo expone una función `_consulta_<entidad>()` que arma el `select()` con los `.options(...)` y la reutilizan `obtener_<entidad>` y `_releer_<entidad>`. Esto evita que una ruta olvide precargar. Alternativa considerada: decorar cada handler; se descarta porque la carga es propiedad de la consulta, no del transporte.
- **D3 — `populate_existing` en la relectura posterior a escritura.** Tras `commit`, con `expire_on_commit=False` la entidad conserva el estado previo; la relectura usa `execution_options(populate_existing=True)` para reemplazar los valores cargados. Alternativa considerada: `session.refresh`; se descarta porque no recarga relaciones de forma fiable.
- **D4 — Verificación por conteo de `SELECT`.** Se registran las sentencias con `before_cursor_execute` y se afirma la cantidad exacta de `SELECT` y la ausencia de consultas por elemento, siguiendo el patrón de `test/altas_relaciones.py`. Alternativa considerada: inspección de `EXPLAIN`; se descarta por fragilidad entre versiones de PostgreSQL.
- **D5 — Sin carga perezosa como mecanismo.** Las relaciones se declaran con `lazy="raise"` implícito por el uso de carga anticipada explícita en las consultas de lectura; si una relación no está precargada, la serialización falla en pruebas en lugar de emitir consultas. Se prefiere detectar en pruebas antes que en producción.
- **D6 — Capacidad nueva (`eager-loading`) en lugar de modificar `crud-endpoints`.** La estrategia de carga es una dimensión ortogonal a la superficie HTTP; modificar `crud-endpoints` mezclaría contratos de ruta con estrategia de consulta. Se introduce una capability nueva y se la vincula con `entity-relationships` (navegación) y `crud-endpoints` (lecturas).

## Risks / Trade-offs

- [Riesgo] Un nuevo read path agregado en el futuro olvide precargar → Mitigación: la función `_consulta_<entidad>()` centraliza la carga y las pruebas de conteo de consultas fallan si se omite.
- [Riesgo] `selectinload` agrega una consulta por colección; en lecturas con varias colecciones el número fijo puede ser mayor → Mitigación: el contrato fija el número exacto por lectura y las pruebas lo verifican; se documenta el límite.
- [Riesgo] `joinedload` sobre colecciones (no usado) generaría multiplicación de filas → Mitigación: la spec prohíbe `joinedload` para colecciones y las pruebas inspeccionan las sentencias.
- [Trade-off] La carga anticipada siempre paga el costo de las relaciones aunque el cliente no las use → Mitigación: se mantienen DTOs de resumen (`LibroResumenRead`, `VentaResumenRead`) sin relaciones para listados, y el detalle carga solo lo que serializa.

## Migration Plan

No aplica: no hay cambios de esquema ni de datos. El change se valida ejecutando los tests existentes y el nuevo caso de verificación de cantidad de consultas; no requiere migración ni despliegue especial. El archivado promoverá `specs/eager-loading/spec.md` a `openspec/specs/eager-loading/spec.md`.

## Open Questions

- (ninguna) — todos los puntos que afectan al contrato, la estrategia o las tareas se resolvieron arriba.
