# Tasks

## 1. Archivos de contenedor

- [x] 1.1 Crear `Dockerfile` en la raíz basado en `python:3.12-alpine`, con capas en orden (requirements primero), usuario sin privilegios `app`, `USER app`, `uvicorn` en `0.0.0.0:8000` y `HEALTHCHECK` con `wget` sobre `http://127.0.0.1:8000/health/ready`. Verificación: `docker build -t libreria .` termina sin error.
- [x] 1.2 Crear `.dockerignore` excluyendo `.env`, `.venv`, `.git` y `__pycache__` (entre otros). Verificación: `docker build` no incluye esos archivos (revisar contexto).

## 2. Verificación de la imagen

- [x] 2.1 Ejecutar `docker build -t libreria .` y confirmar que la imagen base es `python:3.12-alpine` y que la imagen final se construye. Verificación: `docker images` muestra `libreria`.
- [x] 2.2 Ejecutar `docker run -d --name libreria -p 8000:8000 --env-file .env libreria` y verificar que el contenedor queda `healthy` y que los logs muestran el arranque completo con las tablas creadas. Verificación: `docker ps` y `docker logs libreria`.
- [x] 2.3 Verificar que `docker exec libreria id` no es root. Verificación: salida del comando.
- [x] 2.4 Verificar que sin `DATABASE_URL` el contenedor termina con error. Verificación: `docker run --rm libreria` falla y no queda sirviendo.

## 3. Cierre del change

- [x] 3.1 Actualizar `docs/ESTADO.md` para reflejar que el Ejercicio 7 queda cubierto. Verificación: revisión del documento.
- [x] 3.2 Archivar el change con `/opsx-archive 07-imagen-docker`. Verificación: el change aparece en `openspec/changes/archive/`.
