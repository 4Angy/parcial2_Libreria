# Spec Delta

## ADDED Requirements

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
