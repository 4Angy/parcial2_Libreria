# Proposal

## Why

La consigna del parcial (Ejercicio 6, 8 %) exige que al registrar una venta se agenda con `BackgroundTasks` el aviso del comprobante al cliente, simulado con `await asyncio.sleep(0.5)` y un mensaje en el log, que corre después de enviar la respuesta, sin bloquear al servidor. Hoy los handlers ya son `async def` (cubierto por la spec `runtime-lifecycle`), pero `POST /ventas/` no agenda ninguna tarea en segundo plano y no existe ningún uso de `BackgroundTasks`, `asyncio` ni `logging` en `app/`. Formalizarlo cierra la brecha y deja el Ejercicio 6 auditable.

## What Changes

- Se introduce la capability `background-tasks`, que fija el contrato del aviso de comprobante: se agenda en el alta de una venta, corre después de enviar la respuesta, no bloquea el event loop y no accede a la base.
- Se agrega una función async `avisar_comprobante(cliente_id, venta_id)` en `app/modules/ventas/service.py`, usando `await asyncio.sleep(0.5)` y `logging` para registrar el aviso.
- Se modifica `ventas/router.py::crear_venta` para inyectar `BackgroundTasks` y registrar la tarea antes de devolver la respuesta.
- Se agrega verificación del orden (la respuesta se envía antes del aviso) y de que el servidor sigue atendiendo durante el sleep.

## Capabilities

### New Capabilities

- `background-tasks`: contrato del aviso de comprobante en segundo plano al registrar una venta, incluyendo su agendado, su ejecución no bloqueante y su registro en el log.

### Modified Capabilities

- (ninguna) — `runtime-lifecycle` ya cubre los handlers asincrónicos sin bloqueo; este change agrega un comportamiento nuevo (notificación en segundo plano) sin alterar el ciclo de vida de recursos ni la superficie HTTP.

## Impact

- Código afectado: `app/modules/ventas/service.py` (nueva función async), `app/modules/ventas/router.py` (inyección de `BackgroundTasks`).
- Sin cambios en modelos de tabla, esquema de la base ni contratos HTTP (la respuesta de `POST /ventas/` sigue siendo `201` con el mismo cuerpo).
- Sin cambios en Docker, despliegue ni entorno.
- Dependencias: solo biblioteca estándar (`asyncio`, `logging`); no se agregan paquetes.
