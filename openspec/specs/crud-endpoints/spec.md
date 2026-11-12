# crud-endpoints Specification

## Purpose
Define la superficie HTTP del CRUD de referencia: qué rutas existen, con qué método y cuerpo, qué códigos devuelven y cómo se reparten las responsabilidades entre router y servicio.

## Requirements

### Requirement: Rutas del catálogo

La API SHALL exponer las rutas de editoriales, géneros y autores de la tabla de endpoints de referencia, con las altas, lecturas, actualizaciones y sublistados de libros que esa tabla indica.

#### Scenario: Rutas de editoriales

- **WHEN** se solicita `POST /editoriales/`, `GET /editoriales/`, `GET /editoriales/{id}`, `PATCH /editoriales/{id}` o `GET /editoriales/{id}/libros`
- **THEN** cada ruta existe con el método indicado
- **AND** el sublistado devuelve los libros de la editorial

#### Scenario: Rutas de géneros

- **WHEN** se solicita `POST /generos/`, `GET /generos/` o `GET /generos/{id}/libros`
- **THEN** cada ruta existe con el método indicado
- **AND** no existe `PATCH /generos/{id}` porque la tabla de referencia no lo define

#### Scenario: Rutas de autores

- **WHEN** se solicita `POST /autores/`, `GET /autores/{id}`, `PATCH /autores/{id}` o `GET /autores/{id}/libros`
- **THEN** cada ruta existe con el método indicado
- **AND** el sublistado devuelve cada libro con su `rol` y su `orden`

#### Scenario: Editorial, género o autor inexistente en un sublistado

- **WHEN** se solicita un sublistado de libros de una editorial, un género o un autor que no existe
- **THEN** la respuesta es `404`
- **AND** el cuerpo informa que el recurso no existe con un mensaje propio

### Requirement: Rutas de libros

La API SHALL exponer `GET /libros/`, `GET /libros/{id}`, `PATCH /libros/{id}` y `POST /libros/`, y SHALL NOT exponer `PUT` ni `DELETE` sobre un libro.

#### Scenario: Listado y detalle

- **WHEN** se solicita `GET /libros/` o `GET /libros/{id}`
- **THEN** la respuesta es `200` con los libros solicitados
- **AND** el detalle incluye editorial, género y autores

#### Scenario: Actualización de un libro

- **WHEN** se envía `PATCH /libros/{id}` con campos válidos
- **THEN** la respuesta es `200` con el detalle actualizado del libro

#### Scenario: Precio o stock inválido en la actualización

- **WHEN** se envía `PATCH /libros/{id}` con `precio` menor o igual que cero o con `stock` negativo
- **THEN** la respuesta es `422`
- **AND** el libro no se modifica

#### Scenario: Alta de un libro

- **WHEN** se envía `POST /libros/` con un cuerpo que cumple `LibroCreate`
- **THEN** la respuesta es `201` con el detalle del libro creado
- **AND** el `id` del libro lo asigna la base

### Requirement: Rutas de clientes

La API SHALL exponer `POST /clientes/`, `GET /clientes/{id}`, `PATCH /clientes/{id}`, `POST /clientes/{id}/perfil` y `GET /clientes/{id}/ventas`.

#### Scenario: Alta de cliente

- **WHEN** se envía `POST /clientes/` con `nombre` y `email` válidos
- **THEN** la respuesta es `201` con `ClienteRead`
- **AND** el perfil del cliente recién creado es `null`

#### Scenario: Alta de perfil para un cliente existente

- **WHEN** se envía `POST /clientes/{id}/perfil` con un cliente que no tiene perfil
- **THEN** la respuesta es `201` con `PerfilRead`
- **AND** el `cliente_id` del perfil se toma de la ruta y no del cuerpo

#### Scenario: Alta de perfil para un cliente inexistente

- **WHEN** se envía `POST /clientes/{id}/perfil` con un `id` que no corresponde a ningún cliente
- **THEN** la respuesta es `404`
- **AND** no se inserta ningún perfil

#### Scenario: Ventas de un cliente

- **WHEN** se solicita `GET /clientes/{id}/ventas` de un cliente existente
- **THEN** la respuesta es `200` con sus ventas
- **AND** un cliente sin ventas devuelve una lista vacía

### Requirement: Rutas de ventas sin modificación

La API SHALL exponer `GET /ventas/`, `GET /ventas/{id}` y `POST /ventas/`, y SHALL NOT exponer `PATCH /ventas/{id}`.

#### Scenario: Lectura de ventas

- **WHEN** se solicita `GET /ventas/` o `GET /ventas/{id}`
- **THEN** la respuesta es `200` con la venta o las ventas solicitadas
- **AND** el detalle incluye cliente y renglones con `subtotal`

#### Scenario: Modificación de una venta

- **WHEN** se envía `PATCH /ventas/{id}`
- **THEN** la respuesta es `405`
- **AND** la venta no se modifica

#### Scenario: Alta de una venta

- **WHEN** se envía `POST /ventas/` con un cuerpo que cumple `VentaCreate`
- **THEN** la respuesta es `201` con la venta, su cliente y sus renglones
- **AND** la venta queda registrada con la fecha y el total del servidor

### Requirement: Códigos de respuesta del CRUD

La API SHALL responder `201` al crear, `200` al leer o actualizar, `404` cuando el recurso de la ruta no existe, `409` cuando la base rechaza la escritura y `422` cuando el cuerpo o un parámetro no cumplen el contrato.

#### Scenario: Recurso creado

- **WHEN** un alta válida se completa
- **THEN** la respuesta es `201`
- **AND** el cuerpo contiene el recurso con su `id`

#### Scenario: Recurso inexistente

- **WHEN** se solicita por identificador un recurso que no existe
- **THEN** la respuesta es `404`
- **AND** el cuerpo contiene un mensaje propio que nombra el recurso

#### Scenario: Escritura rechazada por la base

- **WHEN** una escritura viola una restricción de la base
- **THEN** la respuesta es `409`
- **AND** la fila no se escribe

#### Scenario: Contrato incumplido

- **WHEN** el cuerpo no valida contra el DTO o un parámetro está fuera de rango
- **THEN** la respuesta es `422`
- **AND** el handler de la ruta no ejecuta la escritura

### Requirement: Separación entre router y servicio

Cada router SHALL ocuparse del transporte HTTP y SHALL delegar la consulta y la escritura al servicio del módulo; el servicio SHALL NOT conocer `HTTPException` ni construir respuestas HTTP.

#### Scenario: Router delgado

- **WHEN** se revisa el `router.py` de un módulo de dominio
- **THEN** declara rutas, códigos de estado y la dependencia de sesión
- **AND** no contiene SQL ni el `try/except` de `IntegrityError`

#### Scenario: Servicio sin HTTP

- **WHEN** se revisa el `service.py` de un módulo de dominio
- **THEN** recibe la sesión y los datos del contrato
- **AND** no importa `HTTPException` ni devuelve códigos de estado

### Requirement: Registro de los routers de dominio

La aplicación SHALL registrar los seis routers de dominio además del router de salud, de modo que todas las rutas queden disponibles al arrancar.

#### Scenario: Rutas disponibles al arrancar

- **WHEN** la aplicación termina su arranque
- **THEN** las rutas de editoriales, géneros, autores, libros, clientes y ventas responden
- **AND** `GET /health/live` y `GET /health/ready` siguen respondiendo `200`

#### Scenario: Documentación de la API

- **WHEN** se consulta `/docs` o `/openapi.json`
- **THEN** aparecen los seis grupos de rutas de dominio con sus etiquetas
- **AND** las rutas de salud conservan su etiqueta
