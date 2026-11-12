# Imagen del proyecto del parcial (Programación III, Unidad 1 a 4).
# Base Alpine para cumplir el límite de 100 MB de la imagen base.
FROM python:3.12-alpine

# Usuario sin privilegios: si alguien vulnera la aplicación, no es dueño del contenedor.
RUN addgroup -S app && adduser -S app -G app

WORKDIR /app

# Capa de dependencias: se cachea mientras requirements.txt no cambie.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código fuente de la aplicación.
COPY . .

# Permisos para el usuario sin privilegios.
RUN chown -R app:app /app
USER app

EXPOSE 8000

# Healthcheck con 127.0.0.1 (no localhost): en Alpine wget resuelve localhost
# primero a IPv6 y uvicorn con --host 0.0.0.0 escucha solo en IPv4.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8000/health/ready || exit 1

# La aplicación crea sus tablas al arrancar (create_all en el lifespan).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]