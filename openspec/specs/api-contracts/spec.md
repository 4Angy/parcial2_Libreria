# api-contracts Specification

## Purpose
Fija la forma de los cuerpos que entran y salen de la API: contratos de alta, de actualización y de lectura separados de las tablas, con la representación serializada que espera la consigna.

## Requirements

### Requirement: Contratos separados de los modelos de tabla

La API SHALL aceptar y devolver DTO y SHALL NOT exponer directamente los modelos de tabla, de modo que un cambio interno de persistencia no altere el contrato HTTP.

#### Scenario: Lectura de una entidad

- **WHEN** se solicita `GET /editoriales/{id}` de una editorial existente
- **THEN** el cuerpo es un `EditorialRead` con `id`, `nombre` y `pais`
- **AND** el cuerpo no incluye atributos de relación ni metadatos del modelo de tabla

#### Scenario: Contrato publicado

- **WHEN** se consulta el esquema OpenAPI de la aplicación
- **THEN** los cuerpos de entrada y de salida de cada ruta se describen con los DTO del módulo
- **AND** ningún esquema de entrada o de salida es un modelo de tabla

### Requirement: Altas sin identificador

Todo DTO de alta SHALL NOT declarar `id` y SHALL rechazar con `422` un cuerpo que incluya `id` o cualquier campo ajeno al contrato.

#### Scenario: Alta con identificador

- **WHEN** se envía `POST /editoriales/` con `{"id": 99, "nombre": "Nueva"}`
- **THEN** la respuesta es `422`
- **AND** no se inserta ninguna fila

#### Scenario: Alta con campo desconocido

- **WHEN** se envía `POST /generos/` con un campo que no pertenece a `GeneroCreate`
- **THEN** la respuesta es `422`
- **AND** no se inserta ninguna fila

#### Scenario: Alta válida

- **WHEN** se envía `POST /autores/` con `nombre` y `nacionalidad`
- **THEN** la respuesta es `201`
- **AND** el cuerpo devuelto es un `AutorRead` con el `id` generado por la base

### Requirement: Actualización parcial de los campos enviados

Todo DTO de actualización SHALL declarar sus campos opcionales y el `PATCH` SHALL escribir únicamente los campos presentes en el cuerpo, sin exigir los ausentes ni borrar los que no se envían.

#### Scenario: Un solo campo enviado

- **WHEN** se envía `PATCH /editoriales/{id}` con `{"pais": "Chile"}`
- **THEN** la respuesta es `200`
- **AND** cambia `pais` y `nombre` conserva su valor anterior

#### Scenario: Cuerpo vacío

- **WHEN** se envía `PATCH /editoriales/{id}` con `{}`
- **THEN** la respuesta es `200`
- **AND** la fila queda sin cambios
- **AND** la respuesta contiene los datos actuales de la editorial

#### Scenario: Campo opcional llevado a nulo

- **WHEN** se envía `PATCH /libros/{id}` con `{"genero_id": null}`
- **THEN** la respuesta es `200`
- **AND** el libro queda sin género
- **AND** los demás campos del libro no cambian

### Requirement: Representación serializada de importes, fechas y enteros

Los importes SHALL serializarse como cadena decimal con dos decimales, las fechas SHALL serializarse en ISO 8601 con zona UTC y sufijo `Z`, y las cantidades y el stock SHALL serializarse como enteros.

#### Scenario: Precio y total

- **WHEN** se lee un libro con `precio = 21000.00` o una venta con `total = 77000.00`
- **THEN** el cuerpo contiene `"precio": "21000.00"` o `"total": "77000.00"` como cadena
- **AND** el valor no se emite como número de punto flotante

#### Scenario: Fecha de venta

- **WHEN** se lee una venta cuya fecha es un instante con zona horaria
- **THEN** el cuerpo contiene una fecha ISO 8601 en UTC terminada en `Z`
- **AND** la fecha no incluye un desplazamiento numérico como `+00:00`

#### Scenario: Cantidades enteras

- **WHEN** se lee un libro o un renglón de venta
- **THEN** `stock` y `cantidad` son números enteros
- **AND** no se emiten como cadenas ni con parte decimal

### Requirement: Relaciones incluidas en las lecturas

Las lecturas que la consigna define con relaciones SHALL incluir los objetos relacionados en el mismo cuerpo, sin exigir peticiones adicionales del cliente.

#### Scenario: Detalle de un libro

- **WHEN** se solicita `GET /libros/{id}`
- **THEN** el cuerpo incluye la editorial, el género y la lista de autores con `rol` y `orden`
- **AND** un libro sin género devuelve `genero` nulo sin fallar

#### Scenario: Detalle de una venta

- **WHEN** se solicita `GET /ventas/{id}`
- **THEN** el cuerpo incluye el cliente y los renglones
- **AND** cada renglón incluye `libro_id`, `titulo`, `cantidad`, `precio_unitario` y `subtotal`

#### Scenario: Perfil de un cliente

- **WHEN** se solicita `GET /clientes/{id}` de un cliente con perfil
- **THEN** `perfil` es un objeto con `id`, `telefono` y `direccion`
- **AND** cuando el cliente no tiene perfil, `perfil` es `null` y nunca una lista
