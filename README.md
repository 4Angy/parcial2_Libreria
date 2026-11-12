# Librería — Parcial 2 (Programación III)

API REST de una librería construida con **FastAPI**, **SQLModel** y
**PostgreSQL async**, como resolución del parcial «Unidad 1 a 4 · Del objeto a la
persistencia».

## Integrantes

- María de los Ángeles Zalazar
- Julieta Cecilia Herrera

## Requisitos

- Docker 20.10+ (opción recomendada)
- PostgreSQL 16 accesible desde la aplicación
- Python 3.12 (solo para levantar sin Docker)

## Estructura

```
app/
  core/        configuración, motor de base, errores, registro de modelos
  modules/     editoriales, generos, autores, libros, clientes, ventas, health
  main.py      aplicación, lifespan y registro de rutas
scripts/       carga de datos iniciales
test/          scripts de verificación y colecciones .http
evidencia/     capturas de los casos de prueba C-07 y D-01 a D-07
Dockerfile     imagen de la aplicación
DEPLOY.md      despliegue en el VPS
```

## Variables de entorno

Copiar `env.example` a `.env` y completar:

```dotenv
DATABASE_URL=postgresql+asyncpg://usuario:password@host:5432/base
SQL_ECHO=false
```

`DATABASE_URL` es obligatoria y debe usar el driver `postgresql+asyncpg`: si
falta, la aplicación falla al arrancar y no queda sirviendo.

## Levantar con Docker

1. Construir la imagen:

   ```bash
   docker build -t libreria .
   ```

2. Ejecutar el contenedor:

   ```bash
   docker run -d --name libreria -p 8000:8000 \
     --env-file .env \
     --add-host=host.docker.internal:host-gateway \
     libreria
   ```

   Si PostgreSQL corre en el host, dentro de `DATABASE_URL` el host debe ser
   `host.docker.internal` (no `localhost`: dentro del contenedor `localhost` es
   el propio contenedor).

3. Cargar los datos iniciales (una sola vez; el esquema lo crea la aplicación al
   arrancar):

   ```bash
   docker exec libreria python scripts/datos_iniciales.py
   ```

4. Verificar:

   ```bash
   curl http://127.0.0.1:8000/health/ready
   curl http://127.0.0.1:8000/libros/
   ```

## Levantar sin Docker

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Documentación de la API

Con la aplicación en marcha:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- Health: `/health/live` (proceso vivo) y `/health/ready` (base disponible)

Recursos principales: `/editoriales/`, `/generos/`, `/autores/`, `/libros/`,
`/clientes/`, `/ventas/`. Los listados aceptan `limit` (1–100, por defecto 20) y
`offset` (≥ 0).

## Verificación

Los scripts de `test/` comprueban los puntos del parcial contra una base
sembrada:

```bash
python test\consultas.py            # lecturas sin N+1
python test\carga_anticipada.py     # carga anticipada de relaciones
python test\altas_relaciones.py     # altas con relaciones
python test\errores_integridad.py   # 409 ante violaciones de integridad
python test\asincronia_background.py# aviso del comprobante en segundo plano
python test\rutas.py                # rutas registradas
python test\serializacion.py        # contratos de lectura
```

## Despliegue

La aplicación está desplegada en <https://libreria.julietaherrera.me>. Los
comandos, la configuración y el procedimiento de actualización están en
[`DEPLOY.md`](DEPLOY.md). Las capturas de los casos de prueba están en
[`evidencia/`](evidencia/).
