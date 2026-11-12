# Design

## Context

Los handlers ya son `async def` y no hay llamadas bloqueantes (cubierto por `runtime-lifecycle`). Falta únicamente el aviso de comprobante al registrar una venta. El router de ventas es delgado y delega en `service.crear_venta`, que devuelve el detalle releído. Ver `proposal.md` — Why.

## Goals / Non-Goals

**Goals:**

- Agendar el aviso con `BackgroundTasks` en `POST /ventas/` sin alterar la respuesta.
- Simular el aviso con `await asyncio.sleep(0.5)` y un log identificable.
- Mantener el router delgado y el servicio testeable.
- No bloquear el event loop ni acceder a la base desde el aviso.

**Non-Goals:**

- No implementar envío real de email ni integración con un proveedor.
- No agregar autenticación/autorización (capítulo 5, fuera de alcance).
- No modificar el alta de ventas ni sus reglas de negocio (cubierto por `04-altas-con-relaciones`).
- No cambiar contratos HTTP ni modelos de tabla.

## Decisions

- **D1 — Ubicación del aviso (Opción A acordada).** Función async `avisar_comprobante(cliente_id, venta_id)` en `app/modules/ventas/service.py`. El router inyecta `BackgroundTasks` y registra la tarea. Alternativa (Opción B: módulo dedicado `notificaciones.py`) se descarta para mantener el cambio mínimo; si se extiende a email real, se puede extraer después.
- **D2 — Firma del aviso.** Recibe `cliente_id: int` y `venta_id: int` (no la sesión). `BackgroundTasks.add_task` acepta funciones async y las ejecuta en el event loop. Alternativa: pasar el objeto `Venta` completo; se descarta porque el aviso no necesita más datos y serializar la entidad fuera de sesión es innecesario.
- **D3 — Logging.** Se usa `logging.getLogger(__name__)` y `logger.info("Comprobante enviado al cliente %s por la venta %s", cliente_id, venta_id)`. El mensaje es identificable en `docker logs` (caso D-07). Alternativa: `print`; se descarta porque no respeta niveles ni configuración del logger.
- **D4 — Orden de ejecución.** `BackgroundTasks` ejecuta las tareas después de enviar la respuesta, en el mismo event loop. El `await asyncio.sleep(0.5)` cede el control, por lo que otras peticiones se atienden durante la espera.
- **D5 — Capacidad nueva (`background-tasks`).** Se crea una capability nueva en lugar de modificar `runtime-lifecycle`, que ya cubre el ciclo de vida de recursos y handlers asincrónicos. El aviso es un comportamiento observable distinto.
- **D6 — Verificación.** Se mide el tiempo de respuesta del `POST /ventas/` (< 0.5s) y se observa el orden en el log. Opcionalmente, un test con `caplog` o captura de stdout.

## Risks / Trade-offs

- [Riesgo] Si `avisar_comprobante` accediera a la sesión cerrada, fallaría en runtime → Mitigación: la firma no recibe sesión y la spec lo prohíbe; las pruebas verifican que no se emiten consultas.
- [Riesgo] Un error no manejado en la tarea en segundo plano se loguea pero no afecta la respuesta ya enviada → Mitigación: envolver el cuerpo del aviso en `try/except` y loguear el error, para que no se pierda silenciosamente.
- [Trade-off] `BackgroundTasks` corre en el mismo proceso; si el proceso muere, el aviso se pierde → Mitigación: aceptable para el alcance del parcial (sin colas ni Redis, fuera de alcance).
- [Trade-off] El aviso usa `asyncio.sleep`, que cede el control; si en el futuro se usara una librería bloqueante, habría que usar `run_in_threadpool` → Mitigación: la spec prohíbe llamadas bloqueantes.

## Migration Plan

No aplica: no hay cambios de esquema ni de datos. El change se valida ejecutando los tests existentes y observando el log. El archivado promoverá `specs/background-tasks/spec.md` a `openspec/specs/background-tasks/spec.md`.

## Open Questions

- (ninguna) — todos los puntos que afectan al contrato, la estrategia o las tareas se resolvieron arriba (Opción A y capability nueva).
