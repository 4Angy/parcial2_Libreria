# Spec Delta

## MODIFIED Requirements

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
