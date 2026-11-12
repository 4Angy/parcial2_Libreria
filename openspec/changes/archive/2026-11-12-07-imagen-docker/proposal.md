# Proposal

## Why

La consigna del parcial (Ejercicio 7, 15 %) exige empaquetar el proyecto en una imagen de Docker con base `python:3.12-alpine`, capas en orden, usuario sin privilegios, sin secretos en la imagen y un `HEALTHCHECK` sobre `GET /health/ready`. Hoy el repositorio no tiene `Dockerfile` ni `.dockerignore`, así que la imagen no se puede construir ni desplegar. Formalizarlo como change deja el trabajo trazable y archivable.

## What Changes

- Se agrega `Dockerfile` en la raíz, basado en `python:3.12-alpine`, que instala dependencias desde `requirements.txt` con `--no-cache-dir` antes de copiar el código, crea un usuario sin privilegios (`app`) y lo activa con `USER`, configura `uvicorn` escuchando en `0.0.0.0:8000` y declara un `HEALTHCHECK` con `wget` sobre `http://127.0.0.1:8000/health/ready`.
- Se agrega `.dockerignore` excluyendo `.env`, `.venv`, `.git` y `__pycache__` (entre otros artefactos no necesarios).
- No se modifican modelos, servicios, routers ni contratos HTTP. Es un change de infraestructura.

## Capabilities

### New Capabilities

- (ninguna) — es un change de infraestructura/tooling (Dockerfile + .dockerignore). No hay cambio de comportamiento observable de la API. `skip_specs: true` en `.openspec.yaml`.

### Modified Capabilities

- (ninguna)

## Impact

- Archivos nuevos en la raíz: `Dockerfile`, `.dockerignore`.
- Sin cambios en `app/`, `openspec/specs/` ni en el esquema de la base.
- Dependencias del sistema: Docker 20.10+ para construir y correr la imagen.
- Riesgo: la imagen base Alpine usa musl; se verificó que las dependencias del stack se instalan sin compilar (consigna §7).
