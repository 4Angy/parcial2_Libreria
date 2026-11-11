# Spec Delta

## Purpose

Define cómo se navega el dominio en los dos sentidos de cada relación, de modo que la aplicación pueda recorrer el grafo de objetos sin consultas manuales por identificador y con la cardinalidad que fija el modelo de dominio.

## ADDED Requirements

### Requirement: Navegación en ambos extremos

Toda relación entre tablas del dominio SHALL declararse en los dos extremos, con cada lado vinculado explícitamente al otro, de modo que asignar un extremo actualice el otro en la misma sesión.

#### Scenario: Recorrido de ida y vuelta

- **WHEN** se asigna una relación desde un extremo y se consulta el objeto por el otro
- **THEN** ambos extremos se referencian mutuamente
- **AND** la navegación funciona en las dos direcciones dentro de la misma sesión

#### Scenario: Relación declarada en un solo extremo

- **WHEN** se revisan las relaciones del dominio
- **THEN** ninguna queda declarada en un único extremo
- **AND** cada extremo declara el vínculo con el nombre del otro

### Requirement: Libro y género como agregación opcional

La relación entre `libro` y `genero` SHALL ser opcional desde el libro: un libro puede no tener género y un género puede agrupar muchos libros.

#### Scenario: Libro sin género

- **WHEN** se consulta un libro cuyo `genero_id` es `NULL`
- **THEN** el acceso al género del libro devuelve un valor nulo
- **AND** la consulta no falla

#### Scenario: Género con varios libros

- **WHEN** se consulta un género que agrupa varios libros
- **THEN** el acceso a los libros del género devuelve la colección completa
- **AND** cada libro de la colección referencia al mismo género

### Requirement: Libro y autor como muchos a muchos con datos

La relación entre `libro` y `autor` SHALL resolverse mediante una entidad de autoría con clase propia que aporta `rol` y `orden`; el acceso a los autores de un libro SHALL hacerse recorriendo sus autorías y SHALL NOT ocultar los datos de la relación.

#### Scenario: Autores de un libro

- **WHEN** se consulta un libro con varias autorías
- **THEN** el acceso a las autorías del libro devuelve una colección de entidades
- **AND** cada autoría expone su `rol`, su `orden` y su autor
- **AND** el autor de cada autoría se alcanza desde la propia autoría

#### Scenario: Libros de un autor

- **WHEN** se consulta un autor que participa en varios libros
- **THEN** el acceso a sus autorías devuelve la colección completa
- **AND** cada autoría referencia al libro correspondiente

#### Scenario: Datos de la relación visibles

- **WHEN** se inspecciona el modelo de la relación entre libros y autores
- **THEN** `rol` y `orden` forman parte de la entidad de autoría
- **AND** la relación no se declara como una tabla de enlace sin clase que esconda esos datos

### Requirement: Cliente y perfil como uno a uno

La relación entre `cliente` y `perfil_cliente` SHALL ser uno a uno, de modo que el acceso al perfil desde un cliente devuelva un objeto y no una colección.

#### Scenario: Perfil como objeto

- **WHEN** se consulta un cliente que tiene perfil
- **THEN** el acceso al perfil devuelve un único objeto
- **AND** el valor no es una lista ni una colección
- **AND** ese perfil referencia al mismo cliente

#### Scenario: Cliente sin perfil

- **WHEN** se consulta un cliente que no tiene perfil
- **THEN** el acceso al perfil devuelve un valor nulo
- **AND** la consulta no falla

### Requirement: Venta y renglón como composición

La relación entre `venta` y `renglon_venta` SHALL ser de composición: los renglones pertenecen a una venta, se acceden desde ella y no sobreviven a su eliminación.

#### Scenario: Renglones de una venta

- **WHEN** se consulta una venta con renglones
- **THEN** el acceso a sus renglones devuelve la colección completa
- **AND** cada renglón referencia a esa misma venta

#### Scenario: Eliminación de la venta

- **WHEN** se elimina una venta con renglones desde la sesión
- **THEN** sus renglones se eliminan con ella
- **AND** no queda ningún renglón sin venta

### Requirement: Venta y cliente como asociación

La relación entre `venta` y `cliente` SHALL permitir navegar del cliente a sus ventas y de cada venta a su cliente, sin que la eliminación de un cliente borre ventas de forma implícita.

#### Scenario: Ventas de un cliente

- **WHEN** se consulta un cliente con ventas registradas
- **THEN** el acceso a sus ventas devuelve la colección completa
- **AND** cada venta referencia al mismo cliente

#### Scenario: Cliente de una venta

- **WHEN** se consulta una venta
- **THEN** el acceso a su cliente devuelve el objeto cliente correspondiente

### Requirement: Renglón y libro como asociación

La relación entre `renglon_venta` y `libro` SHALL permitir navegar del renglón al libro vendido y del libro a los renglones que lo mencionan, conservando el precio unitario histórico del renglón.

#### Scenario: Libro de un renglón

- **WHEN** se consulta un renglón de venta
- **THEN** el acceso a su libro devuelve el libro correspondiente
- **AND** el `precio_unitario` del renglón no cambia cuando cambia el precio del libro

#### Scenario: Renglones que mencionan un libro

- **WHEN** se consulta un libro que aparece en varias ventas
- **THEN** el acceso a sus renglones devuelve todos los renglones que lo mencionan
- **AND** cada renglón referencia a ese libro
