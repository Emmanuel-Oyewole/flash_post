from typing import AsyncGenerator, Any, AsyncIterator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncConnection,
)
from sqlalchemy.orm import DeclarativeBase

from .settings import settings
from .helpers import logger

engine = create_async_engine(settings.postgres_url)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """
    Base class for all models.
    """

    __mapper_args__ = {"eager_defaults": True}


class DatabaseSessionManager:
    """
    Database session manager for handling database connections.
    """

    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            bind=self._engine, autocommit=False, expire_on_commit=False
        )

    async def close(self) -> None:
        """
        Close the database engine.
        """
        if self._engine is None:
            raise Exception("Database engine is not initialized.")

        logger.info("Closing Connection to DB... ")
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None
        logger.info("Connection to DB closed.")

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """
        Context manager for connecting to the database.
        """
        logger.info("Trying to connect to DB...")
        async with self._engine.begin() as connection:
            try:
                logger.info("Connection to DB successful")
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for creating a database session.
        """
        if self._sessionmaker is None:
            raise Exception("Database sessionmaker is not initialized.")
        logger.info("Initializing DB session...")
        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.postgres_url, {"echo": settings.debug})


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.
    """
    async with sessionmanager.session() as session:
        yield session

