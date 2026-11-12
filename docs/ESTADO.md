# Estado del proyecto

**Última actualización:** 11 de noviembre de 2026
**Change activo:** ninguno — el alcance de esta entrega cierra en `04-altas-con-relaciones`, archivado

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
| Change `02` propuesto, diseñado y validado (`--strict`) | ✅ |
| Change `02` implementado y verificado: nueve tablas, restricciones y semilla | ✅ 14/14 tareas |
| Change `03` propuesto, diseñado y validado (`--strict`) | ✅ |
| Change `03` implementado y verificado: DTO, CRUD, paginación y errores | ✅ 22/22 tareas |
| Change `04` propuesto, diseñado y validado (`--strict`) | ✅ |
| Change `04` implementado y verificado: altas con relaciones | ✅ 14/14 tareas |

### Archivos creados (además de los del change 01)

```
app/core/pagination.py         Paginacion(limit, offset) y dependencia con Query
app/core/errors.py             NoEncontrado, Conflicto y confirmar() por SQLSTATE
app/modules/*/schemas.py       DTO Create/Update/Read separados de las tablas
app/modules/*/service.py       consultas, escritura y carga anticipada
app/modules/*/router.py        rutas, códigos y response_model
scripts/datos_iniciales.py     semilla transaccional e idempotente
test/modelos_*.sql|py          verificaciones del change 02
test/contratos.http            altas, lecturas y PATCH parcial
test/paginacion.http           límites, páginas, C-08 y filtro por género
test/errores.http              C-01, C-02, C-03 y ausencia de texto interno
test/lecturas.http             detalle de libro y de venta
test/serializacion.py          Decimal como cadena, fecha UTC con Z
test/consultas.py              ILIKE con parámetro ligado y carga anticipada
test/errores_integridad.py     traducción de IntegrityError
test/rutas.py                  inventario de las 26 rutas publicadas
test/altas.http                altas de libro y de venta, RN-04 a RN-07 y 422
test/altas_relaciones.py       precio copiado, total calculado y consultas fijas
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

### Tareas de `03` (22 de 22)

`1.1`–`1.3`, `2.1`–`2.4`, `3.1`–`3.2`, `4.1`–`4.3`, `5.1`–`5.2`, `6.1`–`6.3`, `7.1`–`7.5`.

Evidencia ejecutada contra la base sembrada y `uvicorn` real:

| Caso | Evidencia |
|---|---|
| Inventario de rutas | `test/rutas.py` → `faltan set() sobran set()`, 24 rutas, sin `POST /libros/` ni `POST /ventas/` |
| Paginación | `limit=0`, `limit=101` y `offset=-1` → 422; `limit=2` con `offset=0` y `offset=2` sin solaparse |
| C-01 | `/editoriales/abc` → 422 sin ejecutar el handler |
| C-02 | Editorial y email repetidos → 409 con mensaje propio, sin `23505`, `_key` ni nombre de restricción |
| C-03 | Segundo perfil del mismo cliente → 409 |
| C-08 | `titulo=' OR '1'='1` → 200 con lista vacía |
| Parámetro ligado | `SQL_ECHO=true` muestra `ILIKE $1::VARCHAR` y el patrón en `parameters` |
| PATCH parcial | `{"pais": "Chile"}` cambia solo `pais`; `{}` responde 200 sin cambios; `{"genero_id": null}` quita el género |
| Detalle de libro | editorial y género como objetos; autores con `rol` y `orden` |
| Detalle de venta | cliente como objeto; renglones con `titulo`, `precio_unitario` y `subtotal`; `fecha` termina en `Z`; `total` es cadena |
| Perfil 1:1 | `GET /clientes/{id}` devuelve `perfil` como objeto o `null`, nunca lista |
| Alcance diferido | `POST /libros/`, `POST /ventas/` y `PATCH /ventas/{id}` → 405 |
| Estado final de la base | `7, 5, 10, 9, 4, 4, 2, 4`; sin filas `Prueba 03` |

### Tareas de `04` (14 de 14)

`1.1`, `2.1`–`2.3`, `3.1`, `4.1`–`4.4`, `5.1`–`5.5`.

Evidencia ejecutada contra la base sembrada y `uvicorn` real:

| Caso | Evidencia |
|---|---|
| Inventario de rutas | `test/rutas.py` → `faltan set() sobran set()`, 26 rutas, con `POST /libros/` y `POST /ventas/` |
| Alta de libro | `POST /libros/` con autorías → 201 con `id` de la base, `precio` como cadena, editorial y género como objetos, autores con `rol` y `orden` |
| Variantes del alta | `autores: []` → 201; `genero_id: null` → 201 con `genero: null`; ISBN repetido → 409 con mensaje propio |
| C-04 | Editorial, género y autor inexistentes → 409 «La referencia indicada no existe.», sin filas residuales |
| C-05 | Cliente inexistente → 409; libro inexistente → 409 «El libro indicado no existe.» |
| C-06 | Venta con dos renglones → 201, `precio_unitario` copiado de cada libro, `subtotal` y `total` calculados (`68900.00` con la semilla actual) |
| RN-06 | `UPDATE` del precio del libro después de la venta: el `precio_unitario` y el `total` guardados no cambian |
| RN-04/RN-05 | `renglones: []`, `libro_id` repetido, `cantidad=0`, `total` o `precio_unitario` en el cuerpo → 422 |
| Contrato del alta | `precio=0`, `stock=-1`, `rol` inválido, `orden=0`, `id` o campo extra en el cuerpo → 422 |
| Consultas del alta | 3 `SELECT` fijos (libros `IN`, venta y renglones), ningún `SELECT` por renglón y ninguno después de la lectura final |
| RN-08 | `PATCH /ventas/{id}` → 405 |
| Estado final de la base | `7, 5, 10, 9, 4, 4, 2, 4` (`libro_autor` en 10); sin filas `Prueba 04` ni `Verif 04` |

**Nota sobre el ejemplo de la consigna.** La consigna muestra una venta con «Rayuela» a `25000.00` y «Respiración artificial» a `27000.00` (total `77000.00`). La semilla del proyecto viene del frontend (`libreria_abc/js/datos-iniciales.js`): libro 1 = «Cien años de soledad» a `24500.00` y libro 4 = «El nombre de la rosa» a `19900.00`, así que el mismo cuerpo da `68900.00`. Se decidió mantener la semilla y verificar la **forma** de la respuesta y la **regla** de cálculo contra los precios reales de la base.

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

## Alcance de la entrega

La entrega cubre los ejercicios **1 a 4** de la consigna, cerrados en los
changes `01` a `04` (todos archivados, con sus specs promovidas a
`openspec/specs/` y la base sembrada en `7, 5, 10, 9, 10, 4, 4, 2, 4`).

Los ejercicios `5` a `8` quedan **fuera de este alcance**. No hay changes
activos ni trabajo pendiente: `openspec list` está vacío y el árbol de Git
está limpio.

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
| `02-modelos-relaciones` | 2 · Modelos, restricciones y relaciones | 22 % | Completo (14/14) |
| `03-contratos-crud` | 3 · Contratos y CRUD | 12 % | Completo (22/22), archivado |
| `04-altas-con-relaciones` | 4 · Altas con relaciones | 17 % | Completo (14/14), archivado |
| `05-lecturas-sin-n1` | 5 · Lecturas sin N+1 | 8 % | Fuera de alcance |
| `06-asincronia-background` | 6 · Asincronía sin bloqueos | 8 % | Fuera de alcance |
| `07-imagen-docker` | 7 · Contenedor | 15 % | Fuera de alcance |
| `08-despliegue-vps` | 8 · Despliegue | 10 % | Fuera de alcance |

---

## Datos que faltan definir

- **Nombre del grupo** — va en el README y en el nombre del `.zip`.
- **Acceso al VPS** y **credenciales de la base de la cátedra** — necesarios para `08`.
- **Puerto asignado por la cátedra** — para el `docker run` de `07`.
