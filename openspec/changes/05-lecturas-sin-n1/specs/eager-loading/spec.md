# Spec Delta

## Purpose

Fija cómo se leen las relaciones del dominio: toda respuesta que incluye datos relacionados los obtiene con carga anticipada declarada en la misma consulta, con un número fijo y verificable de consultas en el detalle de un libro y de una venta, sin depender de la carga perezosa y con las colecciones en un orden estable.

## ADDED Requirements

### Requirement: Estrategia de carga anticipada según la cardinalidad

Toda respuesta que incluya datos de una relación SHALL obtenerlos con carga anticipada declarada en la misma consulta: `joinedload` para relaciones a uno y `selectinload` para colecciones. Ninguna lectura SHALL resolver una relación con una consulta por elemento.

#### Scenario: Detalle de un libro

- **WHEN** se lee el detalle de un libro
- **THEN** la editorial y el género viajan en la consulta del libro
- **AND** las autorías viajan con su autor en una consulta de colección
- **AND** no se emite una consulta por cada autoría

#### Scenario: Detalle de una venta

- **WHEN** se lee el detalle de una venta
- **THEN** el cliente viaja en la consulta de la venta
- **AND** los renglones viajan con su libro en una consulta de colección
- **AND** no se emite una consulta por cada renglón

#### Scenario: Colección con varios hijos

- **WHEN** el libro tiene cinco autorías o la venta tiene cinco renglones
- **THEN** la consulta principal no multiplica filas por la cantidad de hijos
- **AND** la cantidad de consultas es la misma que con un solo hijo

### Requirement: Detalle de un libro con dos consultas fijas

El detalle de un libro que tiene al menos una autoría SHALL resolverse con exactamente dos consultas: una que trae el libro con su editorial y su género, y otra que trae sus autorías con el autor de cada una. El número MUST NOT crecer con la cantidad de autores.

#### Scenario: Libro con un autor

- **WHEN** se lee el detalle de un libro con una autoría
- **THEN** se emiten exactamente dos consultas
- **AND** la respuesta incluye editorial, género y el autor con su rol y su orden

#### Scenario: Libro con cinco autores

- **WHEN** se lee el detalle de un libro con cinco autorías
- **THEN** se emiten exactamente dos consultas
- **AND** el número es el mismo que el del libro con un autor

#### Scenario: Libro sin autorías

- **WHEN** se lee el detalle de un libro sin autorías
- **THEN** la consulta de la colección no se emite
- **AND** la respuesta incluye editorial y género y una lista de autores vacía

### Requirement: Detalle de una venta con dos consultas fijas

El detalle de una venta que tiene al menos un renglón SHALL resolverse con exactamente dos consultas: una que trae la venta con su cliente, y otra que trae sus renglones con el libro de cada uno. El número MUST NOT crecer con la cantidad de renglones.

#### Scenario: Venta con un renglón

- **WHEN** se lee el detalle de una venta con un renglón
- **THEN** se emiten exactamente dos consultas
- **AND** la respuesta incluye el cliente y el renglón con su título, su precio unitario y su subtotal

#### Scenario: Venta con cinco renglones

- **WHEN** se lee el detalle de una venta con cinco renglones
- **THEN** se emiten exactamente dos consultas
- **AND** el número es el mismo que el de la venta con un renglón

#### Scenario: Venta sin renglones

- **WHEN** se lee el detalle de una venta sin renglones
- **THEN** la consulta de la colección no se emite
- **AND** la respuesta incluye el cliente y una lista de renglones vacía

### Requirement: Ninguna lectura depende de la carga perezosa

Una lectura SHALL NOT depender de la carga perezosa: toda relación que la respuesta publica MUST estar cargada al terminar la consulta. Serializar la respuesta MUST funcionar con la sesión cerrada y MUST NOT emitir consultas.

#### Scenario: Serialización con la sesión cerrada

- **WHEN** se serializa el DTO de un libro o de una venta después de cerrar la sesión y el motor
- **THEN** la serialización termina sin error
- **AND** no se emite ninguna consulta
- **AND** las relaciones publicadas conservan sus valores

#### Scenario: Relación no cargada

- **WHEN** una consulta no declara la carga anticipada de una relación que el DTO publica
- **THEN** la verificación falla al serializar con la sesión cerrada
- **AND** el fallo no se resuelve con una carga perezosa implícita

### Requirement: Los DTO de resumen solo publican relaciones cargadas

Los listados SHALL devolver DTO de resumen que no declaran colecciones y cuyas relaciones a uno están cargadas por la propia consulta. El número de consultas de un listado MUST NOT crecer con la cantidad de filas devueltas.

#### Scenario: Listado de libros

- **WHEN** se lista una página de libros
- **THEN** se emite una sola consulta con la editorial y el género de cada libro
- **AND** el listado no incluye autores
- **AND** el número de consultas no depende de la cantidad de libros

#### Scenario: Listado de ventas

- **WHEN** se lista una página de ventas
- **THEN** se emite una sola consulta
- **AND** la respuesta no incluye cliente ni renglones

#### Scenario: Ventas de un cliente

- **WHEN** se listan las ventas de un cliente existente
- **THEN** se emite una consulta para resolver el cliente y una para las ventas
- **AND** no se emite una consulta por venta

### Requirement: Orden estable de las colecciones

La lista `autores` SHALL ordenarse por `orden` ascendente y, ante órdenes iguales, por el identificador del autor. La lista `renglones` SHALL ordenarse por su identificador ascendente. El orden MUST quedar garantizado por el mapeo de la relación, de modo que no dependa del plan de ejecución de la base.

#### Scenario: Autores de un libro

- **WHEN** se lee el detalle de un libro cuyas autorías se insertaron en desorden
- **THEN** la lista `autores` sale ordenada por `orden`
- **AND** dos lecturas consecutivas devuelven la misma secuencia

#### Scenario: Renglones de una venta

- **WHEN** se lee el detalle de una venta cuyos renglones se insertaron en desorden
- **THEN** la lista `renglones` sale ordenada por identificador
- **AND** dos lecturas consecutivas devuelven la misma secuencia
