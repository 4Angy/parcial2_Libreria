# Estado del proyecto

**Última actualización:** 11 de noviembre de 2026
**Change activo:** `01-proyecto-lifespan-health` — 9 de 13 tareas verificadas

---

## Qué es este proyecto

Backend del parcial «Unidad 1 a 4 · Del objeto a la persistencia» de Programación III:
una API de librería con FastAPI, SQLModel, PostgreSQL 16 y despliegue en Docker.
La consigna completa está en `docs/Parcial_Cap1a4_Consigna.pdf`.

**Repositorio:** `C:\Users\zalaz\OneDrive\Desktop\parcialn2`
**Entrega final:** `Parcial_Cap1a4_<NombreDelGrupo>.zip`

---

## Hecho

| Ítem | Estado |
|---|---|
| Repositorio git y `.gitignore` | ✅ |
| OpenSpec inicializado (`schema: spec-driven`, idioma `es`) | ✅ |
| Consigna copiada a `docs/` | ✅ |
| `env.example` sin secretos | ✅ |
| Change `01` propuesto, diseñado y validado (`--strict`) | ✅ |
| Change `01` implementado | ✅ 9/13 tareas verificadas |

### Archivos creados

```
app/main.py                    lifespan, motor, fábrica de sesiones, create_all
app/core/config.py             DATABASE_URL y SQL_ECHO, sin valor por defecto
app/core/database.py           get_session con expire_on_commit=False
app/core/registry.py           punto único de importación de modelos
app/modules/health/router.py   GET /health/live y GET /health/ready
app/modules/{editoriales,generos,autores,libros,clientes,ventas}/
                               andamiaje: models, schemas, service, router
requirements.txt               fastapi[standard], sqlmodel, sqlalchemy[asyncio], asyncpg, python-dotenv
test/health.http               4 casos con resultado esperado
```

### Tareas verificadas de `01`

`1.1`, `1.2`, `2.1`, `2.2`, `2.3`, `3.2`, `4.2`, `5.2`, `5.3`.

La más importante: **`3.2`** — arrancar sin `DATABASE_URL` termina con `EXIT=3`, error
que nombra la variable, y el puerto 8000 no queda escuchando (caso D-05 de la consigna).

---

## Bloqueante

**No hay base de datos disponible.** La causa raíz no es el proyecto:

| Dato | Valor |
|---|---|
| Windows | 11 **Home** Single Language |
| Hyper-V | No disponible (solo Pro/Enterprise) |
| WSL | **No instalado** |
| Docker Desktop | Procesos corriendo, pero sin motor Linux |

Docker Desktop en Windows Home necesita WSL2. Sin WSL, el daemon no responde y
no se puede levantar `postgres:16` en un contenedor.

**Por qué importa para la nota:** los ejercicios 7 (15 %) y 8 (10 %) exigen
`docker build`, `docker run` y una imagen `python:3.12-alpine`. Sin WSL2 no se
pueden entregar.

### Tareas de `01` que quedaron sin marcar

| Tarea | Qué falta |
|---|---|
| `3.1` | Arranque real con `create_all` contra una base |
| `3.3` | Cierre ordenado del motor (`pg_stat_activity` vuelve al valor previo) |
| `4.1` | Respuestas HTTP reales de `/health/ready` y la consulta `SELECT 1` |
| `5.1` | Reconstrucción completa: `.venv`, `.env` con base real, `uvicorn` |

Ninguna se marcó como cumplida sin haberla ejecutado.

---

## Próximo paso

1. Abrir PowerShell **como administrador** y correr:

   ```powershell
   wsl --install
   ```

2. Reiniciar la máquina.
3. Abrir Docker Desktop y esperar a que el daemon responda.
4. Levantar la base:

   ```powershell
   docker run -d --name pg-libreria -p 5432:5432 `
     -e POSTGRES_USER=libreria `
     -e POSTGRES_PASSWORD=<generada> `
     -e POSTGRES_DB=libreria postgres:16
   ```

5. Crear `.env` a partir de `env.example` con la `DATABASE_URL` real.
6. Cerrar las tareas `3.1`, `3.3`, `4.1` y `5.1` del change `01`.
7. Archivar `01` y proponer `02-modelos-relaciones` (22 % de la nota).

### Alternativa sin reinicio

```powershell
winget install -e --id PostgreSQL.PostgreSQL.16
```

Desbloquea los ejercicios 1 a 6 (75 %) sin reiniciar, pero deja los 7 y 8
pendientes hasta instalar WSL2 igual.

---

## Roadmap de changes

| Change | Ejercicio | Peso | Estado |
|---|---|---|---|
| `01-proyecto-lifespan-health` | 1 · Proyecto, conexión y ciclo de vida | 8 % | En curso (9/13) |
| `02-modelos-relaciones` | 2 · Modelos, restricciones y relaciones | 22 % | Pendiente |
| `03-contratos-crud` | 3 · Contratos y CRUD | 12 % | Pendiente |
| `04-altas-con-relaciones` | 4 · Altas con relaciones | 17 % | Pendiente |
| `05-lecturas-sin-n1` | 5 · Lecturas sin N+1 | 8 % | Pendiente |
| `06-asincronia-background` | 6 · Asincronía sin bloqueos | 8 % | Pendiente |
| `07-imagen-docker` | 7 · Contenedor | 15 % | Pendiente |
| `08-despliegue-vps` | 8 · Despliegue | 10 % | Pendiente |

---

## Datos que faltan definir

- **Nombre del grupo** — va en el README y en el nombre del `.zip`.
- **Acceso al VPS** y **credenciales de la base de la cátedra** — necesarios para `08`.
- **Puerto asignado por la cátedra** — para el `docker run` de `07`.
