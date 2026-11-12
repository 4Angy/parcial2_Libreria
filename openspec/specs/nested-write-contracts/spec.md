# nested-write-contracts Specification

## Purpose
Define la forma de los cuerpos de alta que combinan una entidad con sus partes: el libro con sus autorías y la venta con sus renglones, con los ids de lo que ya existe y sin los valores que calcula el servidor.

## Requirements

### Requirement: Contrato de alta de libro con autorías

`LibroCreate` SHALL aceptar `isbn`, `titulo`, `precio`, `stock`, `editorial_id`, un `genero_id` opcional y una lista `autores` cuyos elementos llevan `autor_id`, `rol` y `orden`. SHALL NOT aceptar `id` ni campos ajenos al contrato, tampoco dentro de cada autoría.

#### Scenario: Alta válida con dos autorías

- **WHEN** se envía `POST /libros/` con un `isbn` nuevo, `precio` mayor que cero, `stock` no negativo, `editorial_id`, `genero_id` y dos elementos en `autores` con `autor_id`, `rol` y `orden`
- **THEN** la respuesta es `201` con el detalle del libro
- **AND** el cuerpo incluye `editorial`, `genero` y `autores` con el `rol` y el `orden` de cada autoría
- **AND** el `id` del libro lo asigna la base y no viajó en el cuerpo

#### Scenario: Libro sin género

- **WHEN** se envía `POST /libros/` sin `genero_id` o con `genero_id` nulo
- **THEN** la respuesta es `201` y el libro queda sin género
- **AND** el detalle devuelve `genero` nulo sin fallar

#### Scenario: Alta con identificador

- **WHEN** el cuerpo de `POST /libros/` incluye `id`
- **THEN** la respuesta es `422`
- **AND** no se inserta ningún libro ni ninguna autoría

#### Scenario: Alta con campo desconocido

- **WHEN** el cuerpo de `POST /libros/` incluye un campo que no pertenece a `LibroCreate`
- **THEN** la respuesta es `422`
- **AND** no se inserta ninguna fila

#### Scenario: Autoría con campo desconocido

- **WHEN** un elemento de `autores` incluye un campo que no pertenece al contrato de la autoría
- **THEN** la respuesta es `422`
- **AND** no se inserta ningún libro ni ninguna autoría

### Requirement: Autorías válidas en el alta de libro

Cada autoría SHALL declarar `autor_id`, un `rol` dentro de `autor`, `coautor`, `traductor` e `ilustrador`, y un `orden` mayor o igual que uno. La lista `autores` SHALL poder venir vacía, pero SHALL NOT repetir un `autor_id` ni un `orden` dentro de la misma alta.

#### Scenario: Lista de autorías vacía

- **WHEN** se envía `POST /libros/` con `autores` igual a una lista vacía
- **THEN** la respuesta es `201` con el libro creado y `autores` vacío
- **AND** no se inserta ninguna fila de autoría

#### Scenario: Rol fuera del conjunto permitido

- **WHEN** una autoría envía un `rol` distinto de `autor`, `coautor`, `traductor` o `ilustrador`
- **THEN** la respuesta es `422`
- **AND** no se inserta ningún libro ni ninguna autoría

#### Scenario: Orden menor que uno

- **WHEN** una autoría envía `orden` igual a `0` o negativo
- **THEN** la respuesta es `422`
- **AND** no se inserta ninguna fila

#### Scenario: Precio o stock inválidos

- **WHEN** se envía `POST /libros/` con `precio` menor o igual que cero o con `stock` negativo
- **THEN** la respuesta es `422`
- **AND** no se inserta ningún libro

#### Scenario: Autor repetido en la misma alta

- **WHEN** dos elementos de `autores` declaran el mismo `autor_id`
- **THEN** la respuesta es `422`
- **AND** no se inserta ningún libro ni ninguna autoría

#### Scenario: Orden repetido en la misma alta

- **WHEN** dos elementos de `autores` declaran el mismo `orden`
- **THEN** la respuesta es `422`
- **AND** no se inserta ningún libro ni ninguna autoría

### Requirement: Contrato de alta de venta con renglones

`VentaCreate` SHALL aceptar `cliente_id` y una lista `renglones` no vacía cuyos elementos llevan `libro_id` y `cantidad`. SHALL NOT aceptar `id`, `fecha`, `total`, `precio_unitario`, `subtotal` ni campos ajenos al contrato, tampoco dentro de cada renglón.

#### Scenario: Alta válida con dos renglones

- **WHEN** se envía `POST /ventas/` con un `cliente_id` existente y dos renglones con `libro_id` y `cantidad`
- **THEN** la respuesta es `201` con la venta, su cliente y sus renglones
- **AND** el cuerpo no repite el precio unitario ni el total enviados por el cliente porque no se enviaron

#### Scenario: Venta sin renglones

- **WHEN** se envía `POST /ventas/` con `renglones` igual a una lista vacía
- **THEN** la respuesta es `422`
- **AND** no se inserta ninguna venta

#### Scenario: Total o precio en el cuerpo

- **WHEN** el cuerpo de `POST /ventas/` o uno de sus renglones incluye `total`, `precio_unitario`, `subtotal`, `fecha` o `id`
- **THEN** la respuesta es `422`
- **AND** no se inserta ninguna venta ni ningún renglón

#### Scenario: Renglón con campo desconocido

- **WHEN** un elemento de `renglones` incluye un campo que no pertenece al contrato del renglón
- **THEN** la respuesta es `422`
- **AND** no se inserta ninguna fila

### Requirement: Renglones válidos en el alta de venta

Cada renglón SHALL declarar una `cantidad` mayor que cero y un mismo `libro_id` SHALL NOT aparecer en dos renglones de la misma venta. Un renglón inválido SHALL responder `422` sin llegar a la base.

#### Scenario: Cantidad no positiva

- **WHEN** un renglón envía `cantidad` igual a `0` o negativa
- **THEN** la respuesta es `422`
- **AND** no se inserta ninguna venta

#### Scenario: Libro repetido en dos renglones

- **WHEN** dos renglones de la misma venta declaran el mismo `libro_id`, aunque la cantidad sea distinta
- **THEN** la respuesta es `422`
- **AND** no se inserta ninguna venta ni ningún renglón
