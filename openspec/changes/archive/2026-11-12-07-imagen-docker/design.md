# Design

## Context

El proyecto ya cumple el Ejercicio 1 (lifespan, create_all, /health/ready) y no tiene `Dockerfile` ni `.dockerignore`. La base de datos no forma parte de la imagen: el contenedor la alcanza por red (consigna §7). Ver `proposal.md` — Why.

## Goals / Non-Goals

**Goals:**

- Construir una imagen basada en `python:3.12-alpine` con las dependencias instaladas y el código copiado.
- Capas en orden: primero `requirements.txt` + `pip install`, después el código.
- Usuario sin privilegios (`app`) activado con `USER`.
- Sin secretos en la imagen (`.dockerignore` + sin variables hardcodeadas).
- Uvicorn en `0.0.0.0:8000` con `app.main:app`.
- `HEALTHCHECK` con `wget` sobre `http://127.0.0.1:8000/health/ready`.

**Non-Goals:**

- No incluir PostgreSQL ni Docker Compose (fuera de alcance de la consigna).
- No configurar TLS ni reverse proxy.
- No agregar variables de entorno por defecto: `DATABASE_URL` debe venir de `--env-file`.

## Decisions

- **D1 — Imagen base `python:3.12-alpine`.** Cumple el límite de 100 MB (la base ocupa ~74,7 MB). Alternativa `python:3.12-slim` (180 MB) se descarta por el límite. Se verificó que asyncpg, pydantic-core y el resto se instalan sin compilar.
- **D2 — Orden de capas.** `COPY requirements.txt` + `pip install --no-cache-dir` antes de `COPY .`. Así, un cambio en el código no reinstala dependencias. Alternativa: copiar todo de una vez; se descarta por eficiencia de caché.
- **D3 — Usuario sin privilegios.** Se crea `app:app` con `adduser -S` y se activa con `USER app` antes del `CMD`. El `chown` del directorio de trabajo se hace antes del cambio de usuario. Alternativa: correr como root; se descarta por seguridad (consigna §7).
- **D4 — HEALTHCHECK con `127.0.0.1`.** En Alpine, `wget` resuelve `localhost` primero a IPv6 y uvicorn con `--host 0.0.0.0` escucha solo en IPv4, por lo que el healthcheck fallaría. Se usa `127.0.0.1`. Alternativa: instalar `curl`; se descarta porque Alpine no trae curl y agregarlo aumenta la imagen.
- **D5 — Uvicorn en `0.0.0.0`.** Dentro del contenedor, `127.0.0.1` solo se alcanza desde el propio contenedor; el puerto publicado nunca respondería. Alternativa: `127.0.0.1`; se descarta por inaccesibilidad externa.
- **D6 — Sin secretos en la imagen.** `.dockerignore` excluye `.env`, `.venv`, `.git` y `__pycache__`. `DATABASE_URL` entra por `--env-file` al correr. Alternativa: `ARG`/`ENV` en el Dockerfile; se descarta porque quedan en el historial de capas.
- **D7 — `skip_specs: true`.** Es un change de infraestructura; no hay cambio de comportamiento observable de la API. No se crea capability.

## Risks / Trade-offs

- [Riesgo] `pip install` de asyncpg en Alpine podría requerir compilación en futuras versiones → Mitigación: la consigna verificó que se instala sin compilar; si falla, documentar en `DEPLOY.md`.
- [Riesgo] El `HEALTHCHECK` arranca antes de que `create_all` termine → Mitigación: `--start-period=10s` da margen; si la base es lenta, ajustar.
- [Riesgo] El `.dockerignore` omite `.env` pero un desarrollador podría copiarlo manualmente → Mitigación: la regla dura del proyecto prohíbe secretos en la imagen; revisión en D-01/D-06.
- [Trade-off] La imagen final es más grande que la base (dependencias) → esperado y aceptable (consigna §7).

## Migration Plan

No aplica: no hay cambios de esquema ni de datos. El change se valida con `docker build` y `docker run` (casos D-01, D-02, D-04, D-05, D-06). El archivado no promueve specs (skip_specs).

## Open Questions

- (ninguna) — todos los puntos que afectan al contrato, la estrategia o las tareas se resolvieron arriba.
