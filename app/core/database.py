"""Acceso a la base de datos: dependencia de sesión por petición."""

from collections.abc import AsyncGenerator

from fastapi import Request
from sqlmodel.ext.asyncio.session import AsyncSession


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Entrega una sesión nueva por petición y la cierra al terminar.

    La fábrica vive en `app.state.session_factory`, creada y liberada por el
    `lifespan`. El contexto `async with` cierra la sesión incluso si el
    handler lanza una excepción.
    """
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        yield session
