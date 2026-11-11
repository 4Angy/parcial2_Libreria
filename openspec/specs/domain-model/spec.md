# domain-model Specification

## Purpose
Fija las tablas, columnas, tipos y claves primarias del dominio de la librería, de modo que el esquema creado al arrancar sea el que esperan los casos de prueba, los changes posteriores y la corrección del parcial.

## Requirements

### Requirement: Tablas y columnas obligatorias

El esquema SHALL contener las nueve tablas del dominio con los nombres obligatorios de tabla y de columna, sin renombrar, omitir ni reemplazar ninguna.

#### Scenario: Tabla editorial

- **WHEN** se inspecciona la tabla `editorial`
- **THEN** tiene las columnas `id`, `nombre` y `pais`
- **AND** `nombre` es obligatorio y `pais` admite `NULL`

#### Scenario: Tabla genero

- **WHEN** se inspecciona la tabla `genero`
- **THEN** tiene las columnas `id` y `nombre`
- **AND** `nombre` es obligatorio

#### Scenario: Tabla autor

- **WHEN** se inspecciona la tabla `autor`
- **THEN** tiene las columnas `id`, `nombre` y `nacionalidad`
- **AND** `nombre` es obligatorio y `nacionalidad` admite `NULL`

#### Scenario: Tabla libro

- **WHEN** se inspecciona la tabla `libro`
- **THEN** tiene las columnas `id`, `isbn`, `titulo`, `precio`, `stock`, `editorial_id` y `genero_id`
- **AND** todas son obligatorias salvo `genero_id`, que admite `NULL`

#### Scenario: Tabla libro_autor

- **WHEN** se inspecciona la tabla `libro_autor`
- **THEN** tiene las columnas `libro_id`, `autor_id`, `rol` y `orden`
- **AND** las cuatro son obligatorias
- **AND** la tabla no declara una columna `id` propia

#### Scenario: Tabla cliente

- **WHEN** se inspecciona la tabla `cliente`
- **THEN** tiene las columnas `id`, `nombre` y `email`
- **AND** `nombre` y `email` son obligatorios

#### Scenario: Tabla perfil_cliente

- **WHEN** se inspecciona la tabla `perfil_cliente`
- **THEN** tiene las columnas `id`, `cliente_id`, `telefono` y `direccion`
- **AND** `cliente_id` es obligatorio
- **AND** `telefono` y `direccion` admiten `NULL`

#### Scenario: Tabla venta

- **WHEN** se inspecciona la tabla `venta`
- **THEN** tiene las columnas `id`, `cliente_id`, `fecha` y `total`
- **AND** las cuatro son obligatorias

#### Scenario: Tabla renglon_venta

- **WHEN** se inspecciona la tabla `renglon_venta`
- **THEN** tiene las columnas `id`, `venta_id`, `libro_id`, `cantidad` y `precio_unitario`
- **AND** las cinco son obligatorias

### Requirement: Tipos numéricos exactos para el dinero

Las columnas monetarias SHALL declararse con `Decimal` y precisión y escala explícitas en la base (`NUMERIC(10,2)` o `NUMERIC(12,2)`), y el modelo SHALL NOT usar `float` para ningún importe.

#### Scenario: Precios con dos decimales

- **WHEN** se inspecciona el tipo de `libro.precio` y de `renglon_venta.precio_unitario`
- **THEN** ambas son `NUMERIC(10,2)`

#### Scenario: Total de venta con mayor rango

- **WHEN** se inspecciona el tipo de `venta.total`
- **THEN** es `NUMERIC(12,2)`

#### Scenario: Sin punto flotante en importes

- **WHEN** se revisan los modelos de tabla del dominio
- **THEN** ninguna columna monetaria se declara como `float`, `Float` o `REAL`
- **AND** los valores se leen y escriben como `Decimal`

### Requirement: Fecha de venta con zona horaria

`venta.fecha` SHALL almacenarse como un instante con zona horaria (`TIMESTAMP WITH TIME ZONE`), de modo que el mismo valor represente un momento absoluto sin depender de la zona del proceso.

#### Scenario: Tipo con zona horaria

- **WHEN** se inspecciona el tipo de `venta.fecha`
- **THEN** es `timestamp with time zone`

#### Scenario: Lectura de un instante con desplazamiento

- **WHEN** se guarda una venta con una fecha que incluye desplazamiento horario
- **THEN** la fecha recuperada representa el mismo instante
- **AND** el valor conserva información de zona horaria

### Requirement: Claves primarias del dominio

Cada tabla del dominio SHALL declarar una clave primaria, entera y autogenerada, salvo `libro_autor`, que SHALL usar la clave primaria compuesta (`libro_id`, `autor_id`).

#### Scenario: Clave primaria entera autogenerada

- **WHEN** se inserta una fila sin especificar `id` en `editorial`, `genero`, `autor`, `libro`, `cliente`, `perfil_cliente`, `venta` o `renglon_venta`
- **THEN** la base genera un `id` entero único

#### Scenario: Clave primaria compuesta de libro_autor

- **WHEN** se inspecciona la clave primaria de `libro_autor`
- **THEN** está formada por `libro_id` y `autor_id`
- **AND** no existe una restricción de clave primaria sobre otra columna

### Requirement: Ubicación de cada modelo por módulo

Cada modelo de tabla SHALL declararse en el `models.py` del módulo que le corresponde, de modo que el registro de modelos lo importe sin cambios adicionales.

#### Scenario: Distribución por módulo

- **WHEN** se revisan los `models.py` de los módulos de dominio
- **THEN** `editorial` está en `app/modules/editoriales/models.py`
- **AND** `genero` está en `app/modules/generos/models.py`
- **AND** `autor` está en `app/modules/autores/models.py`
- **AND** `libro` y `libro_autor` están en `app/modules/libros/models.py`
- **AND** `cliente` y `perfil_cliente` están en `app/modules/clientes/models.py`
- **AND** `venta` y `renglon_venta` están en `app/modules/ventas/models.py`

### Requirement: Alta del esquema sin tocar el ciclo de vida

Las tablas nuevas SHALL crearse con el mecanismo de creación de esquema existente, al arrancar la aplicación, sin modificar el `lifespan` ni el registro de modelos.

#### Scenario: Arranque contra una base sin tablas de dominio

- **WHEN** la aplicación arranca contra una base que solo tiene las tablas del change `01`
- **THEN** las nueve tablas del dominio quedan creadas antes de atender peticiones
- **AND** `app/main.py` y `app/core/registry.py` no se modifican

#### Scenario: Reinicio sobre una base ya poblada

- **WHEN** la aplicación se reinicia contra una base que ya tiene las nueve tablas y datos
- **THEN** el arranque no altera las tablas existentes
- **AND** los datos previos se conservan
