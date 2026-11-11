# project-structure Specification

## Purpose
Define la organización obligatoria del proyecto y las dependencias que necesita para arrancar, de modo que todos los módulos compartan la misma estructura y cualquier change posterior sepa dónde vive cada responsabilidad.

## Requirements

### Requirement: Estructura obligatoria de archivos

El proyecto SHALL organizarse por módulo funcional y SHALL exponer, en las rutas exactas de la consigna, la aplicación, la configuración, el acceso a la base, los módulos y la carpeta de pruebas HTTP.

#### Scenario: Rutas obligatorias presentes

- **WHEN** se inspecciona la raíz del proyecto
- **THEN** existen `app/main.py`, `app/core/config.py`, `app/core/database.py`, `requirements.txt`, `env.example` y el directorio `test/`
- **AND** cada módulo de dominio de `app/modules/` expone `models.py`, `schemas.py`, `service.py` y `router.py`
- **AND** `health` expone solo `router.py`, porque no tiene persistencia ni contratos

#### Scenario: Forma de la configuración sin secretos

- **WHEN** se revisa `env.example`
- **THEN** documenta la forma de `DATABASE_URL` con el driver `postgresql+asyncpg` y la variable `SQL_ECHO`
- **AND** no contiene una dirección real, un usuario ni una contraseña

#### Scenario: Módulos mínimos declarados

- **WHEN** se listan los paquetes de `app/modules/`
- **THEN** existen los módulos `health`, `editoriales`, `generos`, `autores`, `libros`, `clientes` y `ventas`
- **AND** los módulos que todavía no tienen lógica de dominio existen como andamiaje importable, sin endpoints ni modelos

### Requirement: Registro único de modelos

El proyecto SHALL concentrar en un único punto la importación de los módulos de modelo que participan de la creación del esquema, de modo que agregar un modelo no requiera modificar el ciclo de vida de la aplicación.

#### Scenario: Alta de un modelo nuevo

- **WHEN** un change posterior agrega un `models.py` a un módulo de dominio
- **THEN** el modelo se incorpora al registro en ese único punto
- **AND** el `lifespan` no se modifica para que la tabla se cree

### Requirement: Dependencias del stack declaradas

El proyecto SHALL declarar en `requirements.txt` las dependencias y versiones mínimas del stack exigido por la consigna, de forma que un entorno limpio se reconstruya con una sola instalación.

#### Scenario: Reconstrucción del entorno

- **WHEN** se instala `requirements.txt` en un entorno virtual vacío
- **THEN** quedan disponibles FastAPI, SQLModel, SQLAlchemy asincrónico, asyncpg, python-dotenv y uvicorn en versiones compatibles con Python 3.12
- **AND** la aplicación puede importarse sin dependencias adicionales

#### Scenario: Compatibilidad con la imagen de entrega

- **WHEN** se revisan las versiones declaradas
- **THEN** ninguna dependencia exige una versión de Python posterior a 3.12
