"""Punto de entrada de la aplicación FastAPI."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.core.registry import import_model_modules
from app.modules.health.router import router as health_router


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
