"""Punto de entrada de la aplicación FastAPI."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.core.errors import ErrorDeDominio
from app.core.registry import import_model_modules
from app.modules.autores.router import router as autores_router
from app.modules.clientes.router import router as clientes_router
from app.modules.editoriales.router import router as editoriales_router
from app.modules.generos.router import router as generos_router
from app.modules.health.router import router as health_router
from app.modules.libros.router import router as libros_router
from app.modules.ventas.router import router as ventas_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Crea los recursos de base al arrancar y los libera al apagar.

    El orden importa: primero la configuración (falla acá si falta
    `DATABASE_URL`), después el registro de modelos y recién entonces el
    motor y la fábrica de sesiones. Publicar los recursos en `app.state`
    permite que `get_session` los use por petición.
    """
    settings = get_settings()
    import_model_modules()

    engine = create_async_engine(settings.database_url, echo=settings.sql_echo)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    app.state.engine = engine
    app.state.session_factory = session_factory

    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        yield
    finally:
        await engine.dispose()


app = FastAPI(title="Parcial Programación III", lifespan=lifespan)
app.include_router(health_router, prefix="/health")
app.include_router(editoriales_router)
app.include_router(generos_router)
app.include_router(autores_router)
app.include_router(libros_router)
app.include_router(clientes_router)
app.include_router(ventas_router)


@app.exception_handler(ErrorDeDominio)
async def manejar_error_de_dominio(
    request: Request, exc: ErrorDeDominio
) -> JSONResponse:
    """Responde un error de negocio con su código y un mensaje propio.

    El cuerpo es `{"detail": mensaje}` y nunca incluye el texto de la base ni
    una traza: los servicios ya tradujeron el rechazo a un mensaje en español.
    """
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.mensaje})


@app.exception_handler(SQLAlchemyError)
async def manejar_error_de_base(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Responde `500` genérico ante una falla de base no traducida.

    Cubre las fallas de lectura o de conexión. Los `IntegrityError` de las
    escrituras ya se convierten en `409` dentro de `app.core.errors.confirmar`.
    """
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor."},
    )
