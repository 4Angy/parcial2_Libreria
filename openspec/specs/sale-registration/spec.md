# sale-registration Specification

## Purpose
Define cómo se registra una venta con sus renglones y cómo se da de alta un libro con sus autorías: una sola transacción por alta, precios copiados del catálogo, total calculado por el servidor y una respuesta que no depende de la carga perezosa.

## Requirements

### Requirement: Alta de venta transaccional con sus renglones

La venta y sus renglones SHALL escribirse en una sola transacción: o se guardan la venta y todos sus renglones, o no se guarda ninguno. Los renglones SHALL crearse dentro del alta de la venta y SHALL NOT existir un alta de renglones por separado.

#### Scenario: Venta con dos renglones

- **WHEN** se envía `POST /ventas/` con un cliente existente y dos renglones válidos
- **THEN** la respuesta es `201` con la venta creada y sus dos renglones
- **AND** la base guarda una fila de venta y una fila de renglón por cada elemento enviado

#### Scenario: Rechazo sin filas parciales

- **WHEN** el alta de la venta es rechazada por la base
- **THEN** la respuesta es `409`
- **AND** no queda ninguna fila de venta ni de renglón de ese intento

#### Scenario: Alta de renglón por separado

- **WHEN** se intenta dar de alta un renglón sin su venta
- **THEN** la API no ofrece una ruta para esa operación
- **AND** los renglones solo existen como parte del alta de una venta

### Requirement: Precio unitario copiado del libro

El servidor SHALL leer `libro.precio` de la base y copiarlo en el `precio_unitario` de cada renglón. El precio SHALL NOT viajar en el cuerpo del alta y SHALL NOT cambiar en la venta registrada aunque el precio del libro cambie después. La lectura de los libros es la necesaria para copiar el precio, no una comprobación previa de existencia.

#### Scenario: Precio copiado del catálogo

- **WHEN** se registra una venta con un libro cuyo precio es `24500.00` y una cantidad de `2`
- **THEN** el renglón creado guarda `precio_unitario` igual a `24500.00`
- **AND** el valor coincide con el precio del libro en la base al momento del alta

#### Scenario: El precio del libro cambia después

- **WHEN** se modifica el precio del libro con `PATCH /libros/{id}` después de registrada la venta
- **THEN** el `precio_unitario` y el `total` de la venta registrada conservan el valor del momento del alta
- **AND** la venta no se modifica

#### Scenario: Libro inexistente en un renglón

- **WHEN** un renglón referencia un `libro_id` que no existe
- **THEN** la respuesta es `409` con un mensaje propio que indica que el libro no existe
- **AND** no se inserta ninguna venta ni ningún renglón

### Requirement: Total calculado por el servidor

El total de la venta SHALL ser la suma de `cantidad` por `precio_unitario` de todos sus renglones, calculada por el servidor y expresada con dos decimales. El total SHALL NOT viajar en el cuerpo del alta.

#### Scenario: Total de dos renglones

- **WHEN** se registra una venta con un renglón de `2` unidades a `24500.00` y otro de `1` unidad a `19900.00`
- **THEN** la respuesta devuelve `total` igual a `68900.00`
- **AND** el total es la suma de los subtotales de los renglones

#### Scenario: Total con dos decimales

- **WHEN** se lee el total de una venta creada
- **THEN** el total se publica como cadena decimal con dos decimales
- **AND** no se emite como número de punto flotante

### Requirement: Fecha del servidor en el alta de venta

La fecha de la venta SHALL asignarla el servidor con el instante UTC del alta y SHALL publicarse en ISO 8601 terminada en `Z`.

#### Scenario: Fecha asignada por el servidor

- **WHEN** se registra una venta válida
- **THEN** la respuesta es `201` con una `fecha` en UTC terminada en `Z`
- **AND** la fecha corresponde al momento del alta y no a un valor del cuerpo

### Requirement: Respuesta del alta con cliente y renglones

El alta de venta SHALL responder el detalle de la venta con su `id`, `fecha` y `total`, el `cliente` con `id`, `nombre` y `email`, y cada renglón con `libro_id`, `titulo`, `cantidad`, `precio_unitario` y `subtotal`. La respuesta SHALL NOT depender de la carga perezosa.

#### Scenario: Forma de la respuesta

- **WHEN** se registra una venta válida
- **THEN** el cuerpo incluye `cliente` como objeto y `renglones` como lista
- **AND** cada renglón incluye el título del libro y su `subtotal`

#### Scenario: Sin consultas por renglón

- **WHEN** se registran las sentencias emitidas durante el alta de una venta con varios renglones
- **THEN** no se emite un `SELECT` por cada renglón
- **AND** después de la lectura final del detalle no se emite ninguna consulta adicional al serializar la respuesta

### Requirement: Alta de libro con autorías en una transacción

El libro y sus autorías SHALL escribirse en una sola transacción y la respuesta SHALL ser el detalle del libro releído con editorial, género y autores. Un ISBN repetido SHALL responder `409` sin dejar filas.

#### Scenario: Alta con autorías

- **WHEN** se envía `POST /libros/` con una editorial existente, un género existente y dos autorías válidas
- **THEN** la respuesta es `201` con el libro y sus dos autorías
- **AND** la base guarda una fila de libro y una fila de autoría por cada elemento enviado

#### Scenario: ISBN repetido

- **WHEN** se envía `POST /libros/` con un `isbn` que ya pertenece a otro libro
- **THEN** la respuesta es `409` con un mensaje propio
- **AND** no queda ninguna fila de libro ni de autoría de ese intento

#### Scenario: Autor inexistente

- **WHEN** una de las autorías referencia un `autor_id` que no existe
- **THEN** la respuesta es `409`
- **AND** no queda ninguna fila de libro ni de autoría de ese intento
