# Spec Delta

## Purpose

Define el contrato del aviso de comprobante al cliente que se agenda en segundo plano al registrar una venta, de modo que la respuesta se envíe sin esperar al aviso y el servidor siga atendiendo otras peticiones mientras se ejecuta.

## ADDED Requirements

### Requirement: Aviso agendado al registrar una venta

Al completarse con éxito el alta de una venta (`POST /ventas/`), la aplicación SHALL agendar una tarea en segundo plano que avise al cliente del comprobante. La respuesta `201` con el detalle de la venta SHALL enviarse antes de que se ejecute el aviso.

#### Scenario: Respuesta antes del aviso

- **WHEN** se envía un `POST /ventas/` válido
- **THEN** la respuesta `201` se envía sin esperar a que se complete el aviso
- **AND** el aviso se ejecuta después de enviar la respuesta

#### Scenario: Venta no registrada

- **WHEN** el alta de la venta falla (por ejemplo, un cliente o libro inexistente)
- **THEN** no se agenda ningún aviso
- **AND** la respuesta es el error correspondiente (`409` o `422`)

### Requirement: Ejecución no bloqueante

El aviso SHALL simularse con una espera asincrónica de `0.5` segundos y SHALL registrarse en el log. Durante esa espera el servidor SHALL seguir atendiendo otras peticiones y el event loop SHALL NOT bloquearse.

#### Scenario: Servidor disponible durante el aviso

- **WHEN** se registra una venta y el aviso está en ejecución
- **THEN** otras peticiones (por ejemplo, `GET /health/live`) responden sin esperar a que termine el aviso
- **AND** el tiempo de respuesta del `POST /ventas/` es menor que `0.5` segundos

#### Scenario: Registro en el log

- **WHEN** el aviso se ejecuta
- **THEN** se registra un mensaje en el log que identifica al cliente y a la venta
- **AND** ese mensaje aparece después de la línea de la respuesta en el registro

### Requirement: Aviso sin acceso a la base

El aviso SHALL NOT acceder a la base de datos ni recibir la sesión. Toda la información necesaria (identificador del cliente y de la venta) SHALL viajar como argumentos de la tarea agendada.

#### Scenario: Sin sesión en el aviso

- **WHEN** se revisa la firma del aviso
- **THEN** no recibe una sesión de base de datos
- **AND** no emite consultas a la base

### Requirement: Handlers asincrónicos sin bloqueo

Todos los handlers de la aplicación SHALL declararse como `async def` y SHALL acceder a la base únicamente mediante el driver asincrónico, sin llamadas bloqueantes dentro del ciclo de la petición.

#### Scenario: Handler asincrónico

- **WHEN** se inspeccionan las rutas registradas
- **THEN** todas están implementadas con `async def`
- **AND** ninguna usa acceso sincrónico a la base ni esperas bloqueantes
