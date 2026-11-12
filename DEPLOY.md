# Despliegue en el VPS

Documento de despliegue del proyecto del parcial «Unidad 1 a 4 · Del objeto a la
persistencia» (Programación III). La aplicación se ejecuta en un contenedor
Docker construido a partir del `Dockerfile` del repositorio y administrado con
EasyPanel sobre un VPS propio. La base de datos PostgreSQL corre fuera del
contenedor de la aplicación.

## URL pública

- **URL:** https://libreria.julietaherrera.me
- **Día y hora del despliegue:** 2026-11-12, 19:28 UTC (16:28, hora local)
- **Estado:** en línea. El servicio debe permanecer activo hasta la publicación
  de las notas, porque la corrección se realiza en vivo.

## Imagen

- **Nombre de la imagen:** `libreria`
- **Imagen base:** `python:3.12-alpine`
- **Contenido:** ~63 MB (la base Alpine queda por debajo del límite de 100 MB)
- **Usuario del proceso:** `app` (`uid=100`), sin privilegios

## Plataforma

- **Panel:** EasyPanel, sobre VPS propio
- **Proyecto:** `app_grupo3`
- **Servicio de la aplicación:** `libreria_backend` (tipo *Aplicación*)
- **Servicio de la base:** `db_libreria` (tipo *PostgreSQL*)
- **Hostname interno de la base:** `db_libreria`
- **Nombre de la base:** `libreria_db`
- **Puerto del contenedor:** `8000`
- **Dominio:** `libreria.julietaherrera.me` → `http://app_grupo3_libreria_backend:8000`

EasyPanel ejecuta el equivalente a `docker build` + `docker run` y publica el
puerto mediante su proxy (Traefik) con HTTPS automático, en lugar de exponer el
puerto del contenedor directamente al exterior.

## Comandos utilizados

### Construcción de la imagen

EasyPanel construye desde el repositorio de GitHub (`4Angy/parcial2_Libreria`,
rama `main`, ruta de compilación `/`). El comando equivalente es:

```bash
docker build -t libreria .
```

### Ejecución del contenedor

EasyPanel administra el contenedor y le inyecta las variables de entorno. El
equivalente manual, con el archivo de variables en el servidor, es:

```bash
docker run -d --name libreria \
  -p 8000:8000 \
  --restart unless-stopped \
  --env-file /opt/libreria/.env \
  --add-host=host.docker.internal:host-gateway \
  libreria
```

### Variables de entorno

Se configuran en EasyPanel → servicio `libreria_backend` → **Entorno**. No se
versionan en el repositorio ni se incluyen en la imagen:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:<password>@db_libreria:5432/libreria_db
SQL_ECHO=false
```

- El driver es `postgresql+asyncpg`, exigido por `app/core/config.py`.
- El host es el **nombre del servicio de base** en EasyPanel (`db_libreria`).
  No se usa `localhost`: dentro del contenedor, `localhost` es el propio
  contenedor de la aplicación.
- La contraseña real vive únicamente en la configuración del panel.

### Carga de datos iniciales

El esquema lo crea la aplicación al arrancar (`create_all` en el `lifespan`), así
que no hay migraciones. La semilla se carga una sola vez desde el Shell del
servicio:

```bash
python scripts/datos_iniciales.py
```

El script es idempotente: si la base ya tiene filas no escribe nada y termina con
código 0; si falla, no confirma ninguna fila.

## Cambios realizados para que corra en el contenedor

- Ninguno sobre la lógica de la aplicación: ya crea sus tablas al arrancar
  (`create_all` en el `lifespan`) y lee `DATABASE_URL` del entorno, sin valor por
  defecto.
- `Dockerfile`: parte de `python:3.12-alpine`, crea el usuario `app`, copia
  `requirements.txt` e instala con `pip install --no-cache-dir` antes de copiar
  el código (para aprovechar la caché de capas), corre con `USER app`, expone
  `8000`, declara `HEALTHCHECK` con `wget` sobre
  `http://127.0.0.1:8000/health/ready` y arranca `uvicorn app.main:app` en
  `0.0.0.0:8000`.
- `.dockerignore`: excluye `.env`, `.venv`, `.git`, `__pycache__`, cachés de
  herramientas y archivos de sistema, de modo que ningún secreto ni entorno
  virtual entre en la imagen.
- El `HEALTHCHECK` usa `127.0.0.1` y no `localhost` porque en Alpine `wget`
  resuelve `localhost` primero a IPv6, mientras que uvicorn escucha en IPv4.

## Cómo actualizar la aplicación

1. Hacer push de los cambios a la rama `main` del repositorio
   (`4Angy/parcial2_Libreria`).
2. En EasyPanel, abrir el servicio `libreria_backend` y presionar
   **Implementar** (o **Forzar recompilación** para ignorar la caché de Docker).
3. Esperar a que el despliegue termine y el servicio quede en ejecución.
4. Verificar `GET /health/ready` y `GET /libros/` contra la URL pública.

Alternativa manual, equivalente:

```bash
git pull
docker build -t libreria .
docker rm -f libreria
docker run -d --name libreria \
  -p 8000:8000 \
  --restart unless-stopped \
  --env-file /opt/libreria/.env \
  --add-host=host.docker.internal:host-gateway \
  libreria
```

Los datos no se pierden al actualizar: viven en el servicio PostgreSQL
(`db_libreria`), no en el contenedor de la aplicación. `create_all` solo crea las
tablas que falten, así que recrear el contenedor no borra información.

## Verificación final

- Servicio `libreria_backend` en ejecución, sin errores en los registros.
- `GET /health/ready` → `200` con `{"estado":"listo","base":"disponible"}`.
- `GET /libros/` → `200` con la lista de libros iniciales.
- `POST /ventas/` → `201` con `precio_unitario` copiado de la base y `total`
  calculado por el servidor.
- Registros del servicio: el aviso del comprobante aparece **después** de la
  línea de respuesta del `POST /ventas/`.

## Evidencia

Las capturas de los casos de prueba están en `evidencia/`. Las que terminan en
`_vps` se tomaron sobre el servidor desplegado; las demás son respaldo local.

| Archivo | Caso |
|---|---|
| `d01_images.txt`, `d01_build_vps.png` | D-01 · Imagen base (`python:3.12-alpine`), Python 3.12 y tamaño de 63 MB |
| `d02_ps.txt`, `d02_logs.txt`, `d02_logs_vps.png` | D-02 · Despliegue en servidor limpio (`Application startup complete`, uvicorn en `0.0.0.0:8000`) |
| `d03_ready.txt`, `d03_libros.txt`, `d03_venta.txt` | D-03 · Acceso desde fuera del servidor (`200`, `200`, `201` con total calculado) |
| `d04_venta_persistida.txt`, `d04_venta_persistida_vps.txt` | D-04 · Recreación del contenedor sin pérdida de datos |
| `d05_no_db.txt` | D-05 · Arranque sin `DATABASE_URL` |
| `d06_user.txt`, `d06_user_vps.png` | D-06 · Usuario del proceso (`uid=100(app)`) |
| `d07_logs.txt`, `d07_logs_vps.png` | D-07 · Aviso del comprobante después de la respuesta |
| `c07_consultas.txt` | C-07 · Consultas del detalle sin N+1 |
