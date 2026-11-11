# Spec Delta

## Purpose

Fija cómo se recorren los listados y cómo se busca en el catálogo: todo listado se pagina con límites validados y la búsqueda por título viaja como parámetro ligado, nunca como SQL armado con texto.

## ADDED Requirements

### Requirement: Paginación obligatoria de todo listado

Todo endpoint que devuelve una lista SHALL aceptar `limit`, entero entre 1 y 100 con valor por defecto 20, y `offset`, entero mayor o igual que 0 con valor por defecto 0. La regla SHALL aplicarse a `/editoriales/`, `/generos/`, `/libros/`, `/ventas/`, `/editoriales/{id}/libros`, `/generos/{id}/libros`, `/autores/{id}/libros` y `/clientes/{id}/ventas`.

#### Scenario: Valores por defecto

- **WHEN** se solicita un listado sin `limit` ni `offset`
- **THEN** la respuesta es `200`
- **AND** devuelve hasta 20 elementos desde el primero

#### Scenario: Límites explícitos

- **WHEN** se solicita `GET /libros/?limit=2&offset=0` y después `GET /libros/?limit=2&offset=2`
- **THEN** ambas respuestas son `200`
- **AND** las dos páginas contienen elementos distintos y no se solapan

#### Scenario: Listado fuera de la tabla de referencia

- **WHEN** se solicita `GET /generos/?limit=2&offset=0` o un sublistado con `limit` y `offset`
- **THEN** la respuesta es `200`
- **AND** la cantidad devuelta respeta el `limit` solicitado

#### Scenario: Offset más allá del total

- **WHEN** se solicita un listado con un `offset` mayor o igual que la cantidad de filas
- **THEN** la respuesta es `200`
- **AND** el cuerpo es una lista vacía

### Requirement: Validación de los parámetros de paginación

La API SHALL responder `422` cuando `limit` está fuera del rango 1–100, cuando `offset` es negativo o cuando cualquiera de los dos no es un entero, y SHALL NOT ejecutar la consulta en esos casos.

#### Scenario: Límite fuera de rango

- **WHEN** se solicita `GET /libros/?limit=0` o `GET /libros/?limit=101`
- **THEN** la respuesta es `422`
- **AND** no se devuelve ningún elemento

#### Scenario: Offset negativo

- **WHEN** se solicita `GET /libros/?offset=-1`
- **THEN** la respuesta es `422`

#### Scenario: Parámetro no entero

- **WHEN** se solicita `GET /libros/?limit=abc` o `GET /libros/?offset=1.5`
- **THEN** la respuesta es `422`

#### Scenario: Límites aceptados

- **WHEN** se solicita un listado con `limit=1`, `limit=100` u `offset=0`
- **THEN** la respuesta es `200`

### Requirement: Orden estable de los listados

Todo listado paginado SHALL devolver sus elementos en un orden determinista y estable entre páginas, de modo que dos páginas consecutivas no repitan ni omitan filas.

#### Scenario: Páginas consecutivas

- **WHEN** se recorren todas las páginas de un listado con un `limit` fijo
- **THEN** la unión de las páginas coincide con el conjunto completo de filas
- **AND** ningún elemento aparece en dos páginas

### Requirement: Búsqueda de libros por título con parámetro ligado

`GET /libros/` SHALL aceptar el parámetro opcional `titulo`, SHALL comparar la parte del título sin distinguir mayúsculas y SHALL enviar el valor como parámetro ligado a la base, nunca concatenado en el texto de la consulta.

#### Scenario: Coincidencia parcial

- **WHEN** se solicita `GET /libros/?titulo=ray`
- **THEN** la respuesta es `200`
- **AND** incluye los libros cuyo título contiene `ray` en cualquier combinación de mayúsculas y minúsculas

#### Scenario: Texto sin coincidencias

- **WHEN** se solicita `GET /libros/?titulo=zzzz`
- **THEN** la respuesta es `200`
- **AND** el cuerpo es una lista vacía

#### Scenario: Intento de inyección

- **WHEN** se solicita `GET /libros/?titulo=' OR '1'='1`
- **THEN** la respuesta es `200`
- **AND** el cuerpo es una lista vacía
- **AND** la consulta ejecutada usa un parámetro ligado y no contiene el texto recibido

#### Scenario: Parámetro ligado visible en el diagnóstico

- **WHEN** se ejecuta la búsqueda con `SQL_ECHO=true`
- **THEN** la consola muestra la consulta con un marcador de parámetro como `$1`
- **AND** el valor buscado aparece en la sección de parámetros, no en el texto de la consulta

### Requirement: Filtro opcional por género

`GET /libros/` SHALL aceptar el parámetro opcional `genero_id` y SHALL devolver únicamente los libros de ese género cuando se envía, combinable con `titulo` y con la paginación.

#### Scenario: Filtro por género

- **WHEN** se solicita `GET /libros/?genero_id=1`
- **THEN** la respuesta es `200`
- **AND** todos los libros devueltos tienen `genero.id` igual a `1`

#### Scenario: Filtro combinado

- **WHEN** se solicita `GET /libros/?titulo=el&genero_id=1&limit=5`
- **THEN** la respuesta es `200`
- **AND** los libros cumplen las dos condiciones y no superan los 5 elementos

#### Scenario: Género sin libros

- **WHEN** se solicita `GET /libros/?genero_id=9999`
- **THEN** la respuesta es `200`
- **AND** el cuerpo es una lista vacía
