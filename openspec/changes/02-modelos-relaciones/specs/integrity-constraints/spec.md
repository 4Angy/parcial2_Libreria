# Spec Delta

## Purpose

Define qué restricciones de integridad hace cumplir la base de datos por sí misma, para que las reglas de negocio del dominio se sostengan aunque la escritura no pase por la aplicación y para que los errores se detecten en PostgreSQL y no en validaciones previas.

## ADDED Requirements

### Requirement: Unicidad del catálogo

La base SHALL rechazar nombres de editorial y de género repetidos y números de ISBN repetidos mediante restricciones `UNIQUE`.

#### Scenario: Editorial con nombre repetido

- **WHEN** se intenta insertar una editorial con un `nombre` ya existente
- **THEN** la base rechaza la operación con una violación de unicidad
- **AND** el error proviene de PostgreSQL, no de una validación de la aplicación

#### Scenario: Género con nombre repetido

- **WHEN** se intenta insertar un género con un `nombre` ya existente
- **THEN** la base rechaza la operación con una violación de unicidad

#### Scenario: Libro con ISBN repetido

- **WHEN** se intenta insertar un libro con un `isbn` ya existente
- **THEN** la base rechaza la operación con una violación de unicidad
- **AND** la fila existente no se modifica

### Requirement: Unicidad de clientes y perfiles

La base SHALL rechazar correos de cliente repetidos y más de un perfil para el mismo cliente mediante restricciones `UNIQUE`.

#### Scenario: Cliente con email repetido

- **WHEN** se intenta insertar un cliente con un `email` ya existente
- **THEN** la base rechaza la operación con una violación de unicidad

#### Scenario: Segundo perfil para el mismo cliente

- **WHEN** se intenta insertar un segundo `perfil_cliente` con un `cliente_id` que ya tiene perfil
- **THEN** la base rechaza la operación con una violación de unicidad

### Requirement: Rango de precio y stock de libro

La tabla `libro` SHALL declarar restricciones `CHECK` que exijan `precio > 0` y `stock >= 0`.

#### Scenario: Precio no positivo

- **WHEN** se intenta insertar o actualizar un libro con `precio` igual a `0` o negativo
- **THEN** la base rechaza la operación con una violación de `CHECK`

#### Scenario: Stock negativo

- **WHEN** se intenta insertar o actualizar un libro con `stock` negativo
- **THEN** la base rechaza la operación con una violación de `CHECK`

#### Scenario: Precio y stock válidos

- **WHEN** se inserta un libro con `precio` mayor que `0` y `stock` igual o mayor que `0`
- **THEN** la base acepta la fila

### Requirement: Rol y orden válidos en la autoría

La tabla `libro_autor` SHALL declarar restricciones `CHECK` que exijan `orden >= 1` y un `rol` dentro de `autor`, `coautor`, `traductor` e `ilustrador`.

#### Scenario: Rol fuera del conjunto permitido

- **WHEN** se intenta insertar una autoría con un `rol` distinto de `autor`, `coautor`, `traductor` o `ilustrador`
- **THEN** la base rechaza la operación con una violación de `CHECK`

#### Scenario: Orden menor que uno

- **WHEN** se intenta insertar o actualizar una autoría con `orden` igual a `0` o negativo
- **THEN** la base rechaza la operación con una violación de `CHECK`

#### Scenario: Autoría válida

- **WHEN** se inserta una autoría con `rol` permitido y `orden` igual o mayor que `1`
- **THEN** la base acepta la fila

### Requirement: Montos y cantidades válidos en ventas

La tabla `venta` SHALL exigir `total >= 0` y la tabla `renglon_venta` SHALL exigir `cantidad > 0` y `precio_unitario > 0`, todas mediante restricciones `CHECK`.

#### Scenario: Total de venta negativo

- **WHEN** se intenta insertar o actualizar una venta con `total` negativo
- **THEN** la base rechaza la operación con una violación de `CHECK`

#### Scenario: Cantidad no positiva

- **WHEN** se intenta insertar o actualizar un renglón con `cantidad` igual a `0` o negativa
- **THEN** la base rechaza la operación con una violación de `CHECK`

#### Scenario: Precio unitario no positivo

- **WHEN** se intenta insertar o actualizar un renglón con `precio_unitario` igual a `0` o negativo
- **THEN** la base rechaza la operación con una violación de `CHECK`

### Requirement: Integridad referencial de las claves foráneas

Cada referencia del dominio SHALL declararse como clave foránea, de modo que la base rechace filas que apunten a un registro inexistente.

#### Scenario: Libro con editorial inexistente

- **WHEN** se intenta insertar un libro cuyo `editorial_id` no existe
- **THEN** la base rechaza la operación con una violación de clave foránea

#### Scenario: Libro con género inexistente

- **WHEN** se intenta insertar un libro cuyo `genero_id` no existe
- **THEN** la base rechaza la operación con una violación de clave foránea

#### Scenario: Renglón con venta inexistente

- **WHEN** se intenta insertar un renglón cuyo `venta_id` no existe
- **THEN** la base rechaza la operación con una violación de clave foránea

#### Scenario: Renglón con libro inexistente

- **WHEN** se intenta insertar un renglón cuyo `libro_id` no existe
- **THEN** la base rechaza la operación con una violación de clave foránea

#### Scenario: Autoría con libro o autor inexistente

- **WHEN** se intenta insertar una autoría cuyo `libro_id` o `autor_id` no existe
- **THEN** la base rechaza la operación con una violación de clave foránea

#### Scenario: Perfil con cliente inexistente

- **WHEN** se intenta insertar un perfil cuyo `cliente_id` no existe
- **THEN** la base rechaza la operación con una violación de clave foránea

#### Scenario: Venta con cliente inexistente

- **WHEN** se intenta insertar una venta cuyo `cliente_id` no existe
- **THEN** la base rechaza la operación con una violación de clave foránea

### Requirement: Borrado en cascada de los renglones

Al eliminar una venta, la base SHALL eliminar sus renglones y SHALL NOT dejar renglones huérfanos ni impedir el borrado.

#### Scenario: Eliminar una venta con renglones

- **WHEN** se elimina una venta que tiene renglones
- **THEN** la operación se completa sin error
- **AND** los renglones de esa venta ya no existen
- **AND** los renglones de otras ventas no se modifican

### Requirement: Índice en cada clave foránea

Cada columna que participa de una clave foránea SHALL tener un índice que la cubra, ya sea propio o como columna líder de la clave primaria o de una restricción de unicidad.

#### Scenario: Índices de las referencias

- **WHEN** se consultan los índices de las tablas del dominio
- **THEN** `libro.editorial_id`, `libro.genero_id`, `libro_autor.autor_id`, `venta.cliente_id` y `renglon_venta.venta_id`, `renglon_venta.libro_id` tienen un índice
- **AND** `libro_autor.libro_id` queda cubierto por la clave primaria compuesta
- **AND** `perfil_cliente.cliente_id` queda cubierto por su restricción de unicidad

#### Scenario: Sin índices redundantes sobre la misma columna

- **WHEN** una columna ya está cubierta por la clave primaria o por una restricción de unicidad
- **THEN** no se declara además un índice simple duplicado sobre esa columna
