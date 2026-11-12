# eager-loading Specification

## Purpose
Define la estrategia de carga anticipada para las lecturas del dominio que serializan relaciones, de modo que ninguna respuesta dependa de la carga perezosa y el número de consultas sea fijo e independiente de la cardinalidad de las colecciones.

## Requirements

### Requirement: Detalle de libro con carga anticipada

La lectura del detalle de un libro (`GET /libros/{id}`) SHALL obtener editorial, género y autorías en la misma consulta que el libro, usando `joinedload` para las relaciones a uno (`editorial`, `genero`) y `selectinload` para la colección de autorías, encadenando `joinedload` para el autor de cada autoría. La cantidad de consultas emitidas SHALL ser fija y SHALL NOT crecer con la cantidad de autores del libro.

#### Scenario: Libro con varios autores

- **WHEN** se solicita el detalle de un libro con varios autores
- **THEN** la respuesta incluye editorial, género y autores con su `rol` y `orden`
- **AND** la cantidad de consultas emitidas es la misma que para un libro con un único autor

#### Scenario: Libro sin género ni autores

- **WHEN** se solicita el detalle de un libro sin género y sin autorías
- **THEN** la respuesta es `200` con `genero` nulo y `autores` vacío
- **AND** la consulta no falla por carga perezosa

#### Scenario: Serialización fuera de sesión

- **WHEN** la sesión se cierra antes de serializar el detalle del libro
- **THEN** la serialización del `LibroRead` se completa sin emitir consultas nuevas
- **AND** no se lanza ningún error de carga perezosa

### Requirement: Detalle de venta con carga anticipada

La lectura del detalle de una venta (`GET /ventas/{id}`) SHALL obtener el cliente y los renglones en la misma consulta que la venta, usando `joinedload` para la relación a uno (`cliente`) y `selectinload` para la colección de renglones, encadenando `joinedload` para el libro de cada renglón. La cantidad de consultas emitidas SHALL ser fija y SHALL NOT crecer con la cantidad de renglones de la venta.

#### Scenario: Venta con varios renglones

- **WHEN** se solicita el detalle de una venta con varios renglones
- **THEN** la respuesta incluye cliente y renglones con `titulo`, `precio_unitario` y `subtotal`
- **AND** la cantidad de consultas emitidas es la misma que para una venta con un único renglón

#### Scenario: Serialización fuera de sesión

- **WHEN** la sesión se cierra antes de serializar el detalle de la venta
- **THEN** la serialización del `VentaRead` se completa sin emitir consultas nuevas
- **AND** no se lanza ningún error de carga perezosa

### Requirement: Estrategia por tipo de relación

Toda lectura que serialice una relación SHALL declarar la carga anticipada en la misma consulta, usando `joinedload` para las relaciones a uno y `selectinload` para las colecciones. La carga perezosa SHALL NOT usarse como mecanismo de lectura en ninguna ruta del dominio.

#### Scenario: Sublistado de libros de una editorial

- **WHEN** se solicita `GET /editoriales/{id}/libros`
- **THEN** cada libro del resultado incluye editorial y género
- **AND** ambos se cargan con `joinedload` en la misma consulta del listado

#### Scenario: Sublistado de participaciones de un autor

- **WHEN** se solicita `GET /autores/{id}/libros`
- **THEN** cada participación incluye su libro con editorial y género
- **AND** el libro y sus referencias se cargan con `joinedload` encadenado

#### Scenario: Cliente con su perfil

- **WHEN** se solicita `GET /clientes/{id}`
- **THEN** el perfil del cliente se incluye en la respuesta
- **AND** se carga con `joinedload` en la misma consulta del cliente

### Requirement: Prohibición de carga perezosa

Ninguna lectura del dominio SHALL depender de la carga perezosa para serializar una relación. Si una relación no está precargada en la consulta, la lectura SHALL fallar de forma explícita en lugar de emitir consultas adicionales durante la serialización.

#### Scenario: Relación no precargada

- **WHEN** se intenta serializar una entidad cuya relación no fue precargada
- **THEN** no se emite ninguna consulta adicional durante la serialización
- **AND** el comportamiento se detecta en las pruebas de carga anticipada

### Requirement: Número fijo de consultas independiente de la cardinalidad

Para cada lectura de detalle (libro y venta), el número de consultas emitidas SHALL ser el mismo independientemente de cuántos autores tenga el libro o cuántos renglones tenga la venta.

#### Scenario: Comparación de cardinalidades

- **WHEN** se leen dos libros, uno con un autor y otro con varios autores
- **THEN** ambas lecturas emiten la misma cantidad de consultas
- **AND** análogamente para dos ventas con distinta cantidad de renglones

#### Scenario: Sin consulta por elemento

- **WHEN** se lee el detalle de un libro con N autores
- **THEN** no se emite una consulta por autor
- **AND** la colección de autorías se obtiene con una única consulta `SELECT IN`
