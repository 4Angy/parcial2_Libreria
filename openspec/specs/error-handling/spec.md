# error-handling Specification

## Purpose
Define cómo la API convierte los rechazos de la base en respuestas estables y sin texto interno, y por qué la unicidad se resuelve escribiendo en lugar de consultando antes.

## Requirements

### Requirement: Unicidad garantizada por la base

La API SHALL NOT consultar si un valor único ya existe antes de escribir; SHALL intentar la escritura y traducir el rechazo de la base a `409` con un mensaje propio. La regla SHALL aplicarse al ISBN del libro, al email del cliente, al nombre de editorial y de género y al perfil único por cliente.

#### Scenario: Editorial repetida

- **WHEN** se envía `POST /editoriales/` con un `nombre` que ya existe
- **THEN** la respuesta es `409`
- **AND** el cuerpo contiene un mensaje propio que indica que ya existe una editorial con ese nombre
- **AND** no se ejecuta una consulta previa de existencia

#### Scenario: Email repetido

- **WHEN** se envía `POST /clientes/` con un `email` que ya existe
- **THEN** la respuesta es `409`
- **AND** el cuerpo contiene un mensaje propio
- **AND** el cliente existente no se modifica

#### Scenario: Segundo perfil del mismo cliente

- **WHEN** se envía `POST /clientes/{id}/perfil` a un cliente que ya tiene perfil
- **THEN** la respuesta es `409`
- **AND** el perfil existente no se modifica
- **AND** la base conserva un solo perfil para ese cliente

#### Scenario: ISBN repetido en una actualización

- **WHEN** se envía `PATCH /libros/{id}` con un `isbn` que ya pertenece a otro libro
- **THEN** la respuesta es `409`
- **AND** ninguno de los dos libros se modifica

### Requirement: Traducción de los errores de integridad

Todo `IntegrityError` de la base SHALL traducirse a `409` con un mensaje propio, cualquiera sea su causa: violación de unicidad, de clave foránea o de una restricción `CHECK`.

#### Scenario: Violación de clave foránea

- **WHEN** se envía `PATCH /libros/{id}` con un `editorial_id` que no existe
- **THEN** la respuesta es `409`
- **AND** el cuerpo contiene un mensaje propio que indica que una referencia no existe
- **AND** el libro no se modifica

#### Scenario: Violación de restricción de rango

- **WHEN** una escritura llega a la base con un valor que viola un `CHECK`
- **THEN** la respuesta es `409`
- **AND** el cuerpo contiene un mensaje propio

#### Scenario: Error de integridad no reconocido

- **WHEN** la base rechaza una escritura con un error de integridad cuya causa no está clasificada
- **THEN** la respuesta es `409` con un mensaje genérico y estable
- **AND** la respuesta no incluye el texto original del error

### Requirement: Respuestas sin texto interno de la base

Ninguna respuesta de error SHALL incluir nombres de tablas, nombres de restricciones, `SQLSTATE`, sentencias SQL ni trazas de la aplicación.

#### Scenario: Cuerpo de un conflicto

- **WHEN** se produce un `409` por unicidad
- **THEN** el cuerpo no contiene `23505`, ni `_key`, ni `duplicate key`, ni el nombre de una tabla
- **AND** el mensaje está en español y describe la regla de negocio

#### Scenario: Cuerpo de un error no controlado

- **WHEN** se produce un error interno no controlado
- **THEN** la respuesta es `500`
- **AND** el cuerpo contiene un mensaje genérico
- **AND** no se expone la traza ni el detalle de la excepción

### Requirement: Sesión recuperable después de un rechazo

Cuando una escritura es rechazada por la base, la sesión de esa petición SHALL descartar la transacción fallida y las peticiones siguientes SHALL seguir funcionando con sesiones nuevas.

#### Scenario: Petición siguiente al conflicto

- **WHEN** una petición recibe `409` por un duplicado y a continuación se envía otra petición válida
- **THEN** la segunda petición responde según su propio contrato
- **AND** no arrastra el estado fallido de la anterior

### Requirement: Traducción centralizada de errores

La traducción de errores SHALL concentrarse en un único punto compartido; los routers SHALL NOT repetir el manejo de `IntegrityError` ni inspeccionar `SQLSTATE`.

#### Scenario: Router sin manejo de base

- **WHEN** se revisan los routers de dominio
- **THEN** ninguno importa `IntegrityError` ni compara códigos `SQLSTATE`
- **AND** todos se apoyan en el mecanismo compartido de errores

#### Scenario: Excepciones de dominio

- **WHEN** un servicio no encuentra un recurso o detecta un conflicto
- **THEN** lanza una excepción de dominio propia
- **AND** el router no construye el cuerpo de error a mano

### Requirement: Referencias inexistentes en las altas

Las altas SHALL NOT consultar si un `editorial_id`, `genero_id`, `autor_id` o `cliente_id` existe antes de escribir: SHALL intentar la escritura y traducir la violación de clave foránea a `409` con un mensaje propio. El mensaje SHALL NOT nombrar tablas ni restricciones, ni incluir el `SQLSTATE` o la traza.

#### Scenario: Libro con editorial inexistente

- **WHEN** se envía `POST /libros/` con un `editorial_id` que no existe
- **THEN** la respuesta es `409` con un mensaje propio
- **AND** no se ejecuta una consulta previa de existencia sobre la editorial
- **AND** el libro y sus autorías no se escriben

#### Scenario: Libro con autor inexistente

- **WHEN** se envía `POST /libros/` con un `autor_id` que no existe
- **THEN** la respuesta es `409` con un mensaje propio
- **AND** no se escribe el libro ni ninguna de sus autorías

#### Scenario: Libro con género inexistente

- **WHEN** se envía `POST /libros/` con un `genero_id` que no existe
- **THEN** la respuesta es `409` con un mensaje propio
- **AND** no se escribe el libro

#### Scenario: Venta con cliente inexistente

- **WHEN** se envía `POST /ventas/` con un `cliente_id` que no existe
- **THEN** la respuesta es `409` con un mensaje propio
- **AND** no se escribe la venta ni ninguno de sus renglones

#### Scenario: Venta con libro inexistente

- **WHEN** se envía `POST /ventas/` con un `libro_id` que no existe
- **THEN** la respuesta es `409` con un mensaje propio
- **AND** no se escribe la venta ni ninguno de sus renglones

#### Scenario: Cuerpo de un conflicto de clave foránea

- **WHEN** se produce un `409` por una referencia inexistente en un alta
- **THEN** el cuerpo no contiene `23503`, ni `_key`, ni el nombre de una tabla o de una restricción, ni una traza
- **AND** el mensaje está en español y describe la referencia faltante sin exponer el texto de la base
