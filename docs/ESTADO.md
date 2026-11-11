# Estado del proyecto

**Última actualización:** 11 de noviembre de 2026
**Change activo:** ninguno — `01-proyecto-lifespan-health` cerrado con 13 de 13 tareas

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
| Change `01` implementado y verificado contra PostgreSQL 16 | ✅ 13/13 tareas |

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

### Tareas de `01` (13 de 13)

`1.1`, `1.2`, `2.1`, `2.2`, `2.3`, `3.1`, `3.2`, `3.3`, `4.1`, `4.2`, `5.1`, `5.2`, `5.3`.

Las verificaciones más relevantes, todas ejecutadas:

| Caso | Evidencia |
|---|---|
| Arranque sin `DATABASE_URL` (D-05) | `uvicorn` termina con `EXIT=3`, el error nombra la variable y el puerto 8000 no queda escuchando |
| Arranque real con base | `uvicorn` levanta, `app.state.engine` y `app.state.session_factory` en `True`, `create_all` ejecutado |
| `/health/live` | 200 `{"estado":"vivo"}` con y sin base |
| `/health/ready` con base | 200 `{"estado":"listo","base":"disponible"}`, `SELECT 1` visible con `SQL_ECHO=true` |
| `/health/ready` sin base | 503 `{"estado":"no_listo","base":"no_disponible"}`, sin texto interno |
| Cierre del motor | `pg_stat_activity` pasa de 2 a 1 conexiones al apagar |

---

## Entorno local (resuelto)

El bloqueante del 11/11 quedó resuelto. **La virtualización nunca fue el problema:**
el hipervisor ya estaba activo porque Windows lo usa para Seguridad Basada en
Virtualización. Lo que faltaba era `VirtualMachinePlatform` y el subsistema WSL,
la capa por la que Docker Desktop habla en Windows Home.

| Dato | Valor |
|---|---|
| Windows | 11 **Home** Single Language (build 26200) |
| CPU | AMD Ryzen 5 7520U — AMD-V activa en BIOS |
| WSL | 3.0.5, versión predeterminada 2 |
| `VirtualMachinePlatform` | habilitada (`vmcompute` presente) |
| Docker Desktop | 29.7.2, motor Linux funcionando |
| PostgreSQL | 16.15 en contenedor `pg-libreria` |

### Trampa a tener presente: hay un PostgreSQL 18 nativo

La máquina tiene instalado **PostgreSQL 18 como servicio de Windows**
(`postgresql-x64-18`), que ocupa `0.0.0.0:5432`. Por eso el contenedor se publica
en **`127.0.0.1:5433`** y la `DATABASE_URL` apunta ahí:

```
DATABASE_URL=postgresql+asyncpg://libreria:<contraseña>@127.0.0.1:5433/libreria
```

Si alguna vez se recrea el contenedor, respetar el puerto 5433 y usar `127.0.0.1`
en lugar de `localhost` (con `localhost` el sistema puede resolver primero `::1`).

```powershell
docker run -d --name pg-libreria -p 127.0.0.1:5433:5432 `
  -e POSTGRES_USER=libreria `
  -e POSTGRES_PASSWORD=<la de .env> `
  -e POSTGRES_DB=libreria `
  --restart unless-stopped `
  postgres:16
```

### Si la instalación de WSL vuelve a fallar

`DISM` devuelve `3010` (éxito, reinicio requerido). Si tras reiniciar `vmcompute`
sigue sin existir, revisar en `C:\Windows\Logs\CBS\CBS.log` si la transacción quedó
en `Pended`. La causa habitual es **Docker Desktop corriendo durante la
habilitación**: hay que cerrarlo antes de repetir `dism /online /enable-feature`.

---

## Próximo paso

1. Archivar `01-proyecto-lifespan-health` (sincroniza las tres delta specs a
   `openspec/specs/`: `project-structure`, `runtime-lifecycle`, `health-checks`).

2. Proponer `02-modelos-relaciones` — 22 % de la nota. Es el change más pesado:
   nueve tablas (`editorial`, `genero`, `autor`, `libro`, `libro_autor`, `cliente`,
   `perfil_cliente`, `venta`, `renglon_venta`), restricciones de unicidad y claves
   foráneas. El dominio sale de la semilla del frontend
   (`libreria_abc\js\datos-iniciales.js`): 7 editoriales, 5 géneros, 10 autores,
   9 libros, 4 clientes, 2 ventas.

### Cómo levantar el entorno en una sesión nueva

```powershell
docker start pg-libreria          # la base (ya tiene --restart unless-stopped)
.venv\Scripts\Activate.ps1        # el entorno
uvicorn app.main:app --reload     # la aplicación
```

Si `.venv` no existe: `python -m venv .venv` y
`.venv\Scripts\python.exe -m pip install -r requirements.txt`.
Si `.env` no existe: copiarlo de `env.example` y poner la contraseña real.

---

## Roadmap de changes

| Change | Ejercicio | Peso | Estado |
|---|---|---|---|
| `01-proyecto-lifespan-health` | 1 · Proyecto, conexión y ciclo de vida | 8 % | Completo (13/13) |
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
