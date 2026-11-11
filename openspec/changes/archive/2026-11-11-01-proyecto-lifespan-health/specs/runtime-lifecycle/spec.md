# Spec Delta

## Purpose

Define cómo la aplicación obtiene su configuración, cuándo crea y libera los recursos de base de datos y cómo entrega una sesión a cada petición, para que el arranque sea determinista y ninguna petición comparta estado de sesión.

## ADDED Requirements

### Requirement: Configuración leída del entorno

La aplicación SHALL leer `DATABASE_URL` y `SQL_ECHO` del entorno, cargando previamente el archivo `.env` cuando exista, y SHALL aceptar únicamente una dirección con el driver asincrónico de PostgreSQL.

#### Scenario: Lectura desde `.env`

- **WHEN** el proceso arranca con un archivo `.env` que define `DATABASE_URL` y `SQL_ECHO`
- **THEN** la configuración expone esa dirección y ese valor de diagnóstico
- **AND** el archivo `.env` no se versiona

#### Scenario: Diagnóstico de consultas configurable

- **WHEN** `SQL_ECHO` vale `true`
- **THEN** cada consulta emitida por SQLAlchemy se escribe en la consola
- **AND** si la variable falta o vale `false`, el diagnóstico queda desactivado

### Requirement: Arranque fallido sin dirección de base

El proyecto SHALL NOT definir una dirección de base por defecto. Si `DATABASE_URL` falta o está vacía, el arranque SHALL terminar con un error y el proceso SHALL NOT quedar atendiendo peticiones.

#### Scenario: Arranque sin `DATABASE_URL`

- **WHEN** se inicia la aplicación sin `DATABASE_URL` en el entorno ni en `.env`
- **THEN** el proceso termina con código de salida distinto de cero
- **AND** no queda ningún puerto escuchando
- **AND** el mensaje de error identifica la variable faltante sin exponer credenciales

### Requirement: Recursos de base en el ciclo de vida

La aplicación SHALL crear el motor asincrónico y la fábrica de sesiones durante el arranque, SHALL publicarlos en el estado de la aplicación y SHALL cerrar el motor durante el apagado.

#### Scenario: Recursos disponibles después del arranque

- **WHEN** la aplicación termina su arranque
- **THEN** el estado de la aplicación expone el motor y la fábrica de sesiones
- **AND** ambos son los mismos objetos usados por las peticiones

#### Scenario: Cierre ordenado

- **WHEN** la aplicación se apaga
- **THEN** el motor se cierra y libera sus conexiones
- **AND** no quedan recursos de base abiertos

### Requirement: Una sesión por petición

Cada handler que accede a la base SHALL recibir su sesión mediante la dependencia `get_session`, SHALL obtener una sesión nueva por petición y esa sesión SHALL crearse con `expire_on_commit=False`.

#### Scenario: Sesiones independientes

- **WHEN** dos peticiones se atienden de forma concurrente
- **THEN** cada una recibe una sesión distinta
- **AND** al terminar la petición la sesión se cierra

#### Scenario: Atributos disponibles después del commit

- **WHEN** un handler confirma una escritura y luego lee atributos del objeto
- **THEN** los atributos siguen accesibles sin emitir una consulta adicional
- **AND** la sesión no queda en estado expirado

### Requirement: Creación del esquema al arrancar

Durante el arranque, la aplicación SHALL crear las tablas que falten a partir de los metadatos de SQLModel, con todos los modelos registrados ya importados, y SHALL NOT modificar las tablas existentes.

#### Scenario: Base vacía

- **WHEN** la aplicación arranca contra una base sin tablas
- **THEN** todas las tablas de los modelos registrados quedan creadas antes de atender peticiones

#### Scenario: Base ya creada

- **WHEN** la aplicación arranca contra una base que ya tiene las tablas
- **THEN** el arranque no altera ni elimina las tablas existentes
- **AND** los datos previos se conservan

#### Scenario: Base inaccesible

- **WHEN** la aplicación no puede conectarse a la base durante el arranque
- **THEN** el arranque falla con un error
- **AND** el proceso no queda sirviendo peticiones

### Requirement: Handlers asincrónicos sin bloqueo

Todos los handlers de la aplicación SHALL declararse como `async def` y SHALL acceder a la base únicamente mediante el driver asincrónico, sin llamadas bloqueantes dentro del ciclo de la petición.

#### Scenario: Handler asincrónico

- **WHEN** se inspeccionan las rutas registradas
- **THEN** todas están implementadas con `async def`
- **AND** ninguna usa acceso sincrónico a la base ni esperas bloqueantes
