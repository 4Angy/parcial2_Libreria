# parcial2_Libreria — Instrucciones para Agentes

> Este archivo (y su copia sincronizada) es lo PRIMERO que todo agente lee al entrar al repo.
> Derivado de `docs/Parcial_Cap1a4_Consigna.pdf` (la consigna del parcial), `docs/ESTADO.md` y `openspec/`.
> No existe `knowledge-base/` todavía: la fuente de verdad actual es `docs/ESTADO.md` + `openspec/specs/` + la consigna.
> Si se quiere generar la KB, correr `kb-creator`.

---

## Stack Tecnológico

| Capa | Tecnología | Versión mínima |
|------|------------|----------------|
| Lenguaje | Python | 3.12 |
| Framework web | FastAPI (handlers `async def`) | 0.111 |
| Modelos de tabla y contratos | SQLModel | 0.0.24 |
| Motor / sesión / carga anticipada | SQLAlchemy (async) | 2.0 |
| Driver PostgreSQL async | asyncpg | 0.30 |
| Base de datos | PostgreSQL | 16 |
| Variables de entorno | python-dotenv | 1.0 |
| Servidor ASGI | uvicorn (instalado por `fastapi[standard]`) | — |
| Contenedor | Docker | 20.10 |
| Imagen base | `python:3.12-alpine` | — |

Detalle completo de uso: `docs/Parcial_Cap1a4_Consigna.pdf` §Requisitos técnicos. Configuración por entorno: `env.example`.

---

## Base de Conocimiento

No hay carpeta `knowledge-base/` en este repo. La fuente de verdad del dominio y del estado del proyecto vive en:

| Archivo / carpeta | Cuándo leerlo |
|---|---|
| `docs/Parcial_Cap1a4_Consigna.pdf` | Consigna completa del parcial: dominio, modelo, RN, endpoints, contenedor, despliegue, casos de prueba, criterios |
| `docs/ESTADO.md` | Estado real del proyecto: qué changes están hechos, evidencia, entorno local, alcance de la entrega |
| `openspec/config.yaml` | Schema `spec-driven`, idioma `es` |
| `openspec/specs/` | Specs promovidas (fuente de verdad de los contratos vigentes) |
| `openspec/changes/archive/` | Historial de changes archivados con proposal/design/tasks/specs |

> ⚠️ Antes de implementar un change nuevo, leer `docs/ESTADO.md` (alcance y roadmap) y `openspec/specs/` (contratos vigentes). La consigna manda sobre cualquier otra fuente.

---

## Skills Disponibles

No existe `.atl/skill-registry.md`. Skills relevantes para este proyecto (cargá la que corresponda ANTES de escribir código):

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| **Backend Core** | FastAPI / SQLModel / SQLAlchemy async / relaciones | `python-design-patterns`, `python-error-handling`, `python-code-style`, `postgresql-table-design`, `supabase-postgres-best-practices` |
| **Backend Async** | Asincronía, BackgroundTasks, carga anticipada | `async-python-patterns`, `python-performance-optimization` |
| **Tests** | pytest, validación de contratos y modelos | `python-testing-patterns` |
| **Contenedor / DevOps** | Dockerfile, imagen, despliegue | `multi-stage-dockerfile` |
| **Orquestación** | SDD / OPSX / docs | `openspec-explore`, `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, `openspec-sync-specs`, `openspec-update-change`, `opencode` |

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; no versionado — no está en el repo). Esta tabla solo mapea skill→rol.

---

## Roadmap de Changes

Plan operativo en `docs/ESTADO.md` §Roadmap de changes. Resumen:

- **Changes cerrados (01–04)**, todos archivados con specs promovidas:
  - `01-proyecto-lifespan-health` — Proyecto, conexión y ciclo de vida (8 %).
  - `02-modelos-relaciones` — Modelos, restricciones y relaciones (22 %).
  - `03-contratos-crud` — Contratos y CRUD (12 %).
  - `04-altas-con-relaciones` — Altas con relaciones (17 %).
- **Fuera del alcance actual (05–08)**: lecturas sin N+1 (8 %), asincronía/background (8 %), imagen Docker (15 %), despliegue en VPS (10 %). No hay changes activos; `openspec list` vacío.

**Antes de cualquier `/opsx:propose`**: leer `docs/ESTADO.md`, identificar dependencias del change y los archivos de "Leer antes" en `openspec/specs/`.

---

## Reglas Duras (específicas del proyecto)

> Reglas **globales** ya definidas en `~/.claude/CLAUDE.md` (orquestador, governance, TDD, engram): el proyecto las **hereda**, no se repiten acá.

Acá viven las reglas específicas de este proyecto, derivadas de la consigna y del stack (FastAPI + SQLModel + PostgreSQL async). Son contrato; romperlas es un defecto. Formato `NUNCA X → hacer Y`:

### Modelo y persistencia

- NUNCA usar `float` para dinero → usar `Decimal` y columnas `Numeric` (`Numeric(10,2)` para precio unitario, `Numeric(12,2)` para total).
- NUNCA dejar una FK sin índice explícito → PostgreSQL no indexa FKs por sí solo; declarar `index=True`.
- NUNCA modelar `libro_autor` como tabla de enlace sin clase → es una entidad con `rol` y `orden` (objeto de asociación). Para ir de libro a autores: `libro.autorias[i].autor`.
- NUNCA dejar una relación de uno a uno como lista → `Cliente.perfil` devuelve un objeto (o `null`), nunca una lista.
- NUNCA declarar navegación en un solo extremo → `Relationship(back_populates=...)` en ambos lados de cada FK.
- NUNCA depender de la carga perezosa → toda relación que se serializa se precarga en la misma consulta (`joinedload` para a-uno, `selectinload` para colecciones).
- NUNCA armar SQL por concatenación de texto con datos del usuario → usar parámetros ligados (ej. `ilike` con el patrón como parámetro).
- NUNCA verificar unicidad con una consulta previa → delegarla a la base (`UNIQUE`) y traducir `IntegrityError` a `409` con mensaje propio.
- NUNCA enviar texto interno de la base al cliente (nombres de tablas, restricciones, trazas, SQLSTATE) → traducir `IntegrityError` a mensaje propio en `app.core.errors.confirmar`.

### Contratos y HTTP

- NUNCA mezclar modelos de tabla con DTOs → `Create`/`Update`/`Read` separados en `schemas.py`; los de alta no llevan `id`.
- NUNCA aceptar campos no declarados en un DTO → `model_config = ConfigDict(extra="forbid")`.
- NUNCA aplicar un `PATCH` sobre todos los campos → usar `model_dump(exclude_unset=True)` y aplicar solo los enviados.
- NUNCA responder con código incorrecto → `201` al crear, `404` si no existe, `409` si la base rechaza la escritura, `422` si el cuerpo/parámetros no cumplen el contrato.
- NUNCA paginar sin `limit` (1–100, default 20) y `offset` (≥ 0) → restricciones en `Query`; fuera de rango responde `422` sin ejecutar el handler.
- NUNCA aceptar en el alta de un libro un `if` previo que consulte si un id existe → escribir a ciegas y dejar que la base rechace la FK (→ `409`).
- NUNCA hacer que el precio unitario o el total de una venta viajen en el DTO → el servidor los copia/calcula (RN-06, RN-07).
- NUNCA permitir `PATCH` de ventas → las ventas no se modifican (RN-08); el path responde `405`.
- NUNCA permitir venta sin al menos un renglón ni repetir un libro en dos renglones → validación del DTO (RN-05); `422`.
- NUNCA crear renglones por separado → la venta se crea con sus renglones en un solo alta (RN-04).

### Asincronía

- NUNCA escribir un handler síncrono ni ejecutar llamadas bloqueantes dentro de él (`time.sleep`, `requests`, acceso síncrono a la base) → todos los handlers `async def`.
- NUNCA depender de la carga perezosa en serialización → precargar en la consulta (ver arriba).
- NUNCA enviar la respuesta antes de agendar el aviso → al registrar una venta, agendar con `BackgroundTasks` el aviso del comprobante (simulado con `await asyncio.sleep(0.5)` y log), que corre después de enviar la respuesta.

### Estructura y ciclo de vida

- NUNCA crear el motor/sesión fuera del `lifespan` → se crean en `lifespan`, se guardan en `app.state`, se cierran al apagar.
- NUNCA usar una sesión compartida entre peticiones → una por petición con `Depends(get_session)`, `expire_on_commit=False`.
- NUNCA hardcodear `DATABASE_URL` ni dejar un valor por defecto → se lee del entorno (`.env`); falta → el arranque falla antes de abrir conexión.
- NUNCA omitir un modelo del registro → `app.core.registry.MODEL_MODULES` debe listar todos los módulos de modelos para que `create_all` cree sus tablas.
- NUNCA modificar el esquema con `create_all` esperando alterar tablas existentes → `create_all` solo crea las que faltan; los cambios de modelo no llegan a una base ya creada.

### Contenedor y despliegue

- NUNCA usar una imagen base distinta de `python:3.12-alpine` → límite de 100 MB y superficie de ataque.
- NUNCA correr la app como `root` → crear usuario sin privilegios y activarlo con `USER`.
- NUNCA incluir secretos en la imagen → `.dockerignore` excluye `.env`, `.venv`, `.git`, `__pycache__`; la URL/contraseña de la base entran por `--env-file` al correr.
- NUNCA hornear secretos en una capa aunque una posterior los borre → quedan en el historial de la imagen.
- NUNCA escuchar en `127.0.0.1` dentro del contenedor → `uvicorn` en `0.0.0.0` (si no, el puerto publicado no responde).
- NUNCA usar `localhost` en el `HEALTHCHECK` de Alpine → usar `127.0.0.1` (wget resuelve `localhost` primero a IPv6 y uvicorn escucha solo en IPv4).
- NUNCA usar `localhost` para la base dentro del contenedor → dentro del contenedor `localhost` es el propio contenedor; si la base corre en el host, usar `host.docker.internal` (en Linux habilitar con `--add-host=host.docker.internal:host-gateway`) o la dirección que provea la cátedra.
- NUNCA dejar la app sirviendo si la base no responde → el arranque falla y el contenedor termina con error.

### Entrega

- NUNCA incluir `.venv`, `__pycache__` ni `.env` en el `.zip` → el entorno se reconstruye con `requirements.txt`.
- NUNCA subir credenciales reales al repo, a la imagen ni al `.zip` (ni en el historial de git) → si alguna vez se subió una, cambiarla.
- NUNCA entregar sin `README.md` (integrantes + pasos para levantar) ni `DEPLOY.md` (URL pública, fecha/hora, comandos completos, cambios, cómo actualizar).
- NUNCA entregar sin la carpeta `evidencia/` con la salida de C-07 y los casos D.

---

## Flujo de Trabajo

```
1. Leer la consigna (docs/Parcial_Cap1a4_Consigna.pdf) y docs/ESTADO.md  → entender el dominio y el estado
2. Identificar el change en openspec / ESTADO.md                      → respetar dependencias
3. /opsx:propose C-NN-nombre                                         → proposal + design + specs + tasks
4. Implementar las tasks (cargando skills)                            → respetando las reglas duras
5. /opsx:archive C-NN-nombre + marcar [x]                             → cerrar el change
```

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la consigna y este archivo, las reglas duras prevalecen. Ante conflicto entre la consigna y el código existente, la consigna manda.
