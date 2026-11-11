# Spec Delta

## Purpose

Define el contenido y el comportamiento del script que puebla la base de desarrollo con la semilla del frontend, para que el dominio quede demostrable con datos reales y para que la carga sea repetible sin duplicar filas.

## ADDED Requirements

### Requirement: Script de datos iniciales ejecutable

El proyecto SHALL incluir un script ejecutable con el entorno virtual del proyecto que cargue la semilla del frontend en la base configurada por `DATABASE_URL`, con las cantidades exactas del origen.

#### Scenario: Carga completa sobre una base vacía

- **WHEN** se ejecuta el script contra una base sin datos de dominio
- **THEN** el proceso termina sin error
- **AND** la base queda con 7 editoriales, 5 géneros, 10 autores, 9 libros, 4 clientes, 4 perfiles, 2 ventas y 4 renglones de venta

#### Scenario: Ejecución sin base disponible

- **WHEN** se ejecuta el script con una `DATABASE_URL` que no conecta
- **THEN** el proceso termina con un mensaje de error explícito
- **AND** no deja datos parciales confirmados

### Requirement: Correspondencia con la semilla del frontend

Los datos cargados SHALL conservar la información de la semilla del frontend traducida al modelo nuevo, con identificadores enteros, importes como `Decimal`, autorías con `rol` y `orden`, un perfil por cliente y el precio unitario histórico de cada renglón.

#### Scenario: Catálogo traducido

- **WHEN** se consultan editoriales, géneros, autores y libros después de la carga
- **THEN** los nombres coinciden con la semilla del frontend
- **AND** cada libro conserva su ISBN y su precio original
- **AND** el libro sin género en la semilla queda con `genero_id` nulo

#### Scenario: Autorías con datos de la relación

- **WHEN** se consultan las autorías de los libros cargados
- **THEN** cada libro tiene al menos una autoría
- **AND** el primer autor de cada libro figura con `rol` `autor` y `orden` `1`
- **AND** el segundo autor del libro que tiene dos queda con `rol` `coautor` y `orden` `2`

#### Scenario: Perfil uno a uno por cliente

- **WHEN** se consultan los clientes cargados
- **THEN** cada cliente tiene exactamente un perfil asociado
- **AND** el perfil se alcanza desde el cliente como un objeto

#### Scenario: Renglones con precio histórico

- **WHEN** se consultan los renglones de las ventas cargadas
- **THEN** cada renglón copia el precio unitario del libro en el momento de la carga
- **AND** el total de cada venta coincide con la suma de `cantidad` por `precio_unitario` de sus renglones
- **AND** la fecha de cada venta conserva el día de la semilla como instante con zona horaria

### Requirement: Carga sin duplicados

El script SHALL NOT duplicar datos: si la base ya contiene filas de dominio, SHALL advertirlo de forma visible y SHALL dejar la base sin cambios.

#### Scenario: Segunda ejecución sobre una base poblada

- **WHEN** se ejecuta el script por segunda vez sobre la misma base
- **THEN** el proceso informa que ya hay datos cargados
- **AND** las cantidades de filas no cambian
- **AND** no se genera ningún error de unicidad

#### Scenario: Base parcialmente poblada

- **WHEN** se ejecuta el script sobre una base que ya tiene filas en alguna de las tablas del dominio
- **THEN** el proceso se detiene sin escribir
- **AND** la base conserva exactamente las filas que tenía
