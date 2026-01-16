"""
Database connection management for Economic Policy Engine
Supports PostgreSQL with connection pooling and async operations
"""

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import Optional, AsyncGenerator, Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database connection manager with support for both sync and async operations
    """

    def __init__(self, database_url: str,
                 pool_size: int = 20,
                 max_overflow: int = 10,
                 echo: bool = False):
        """
        Initialize database manager

        Args:
            database_url: PostgreSQL connection URL
            pool_size: Connection pool size
            max_overflow: Max overflow connections
            echo: Echo SQL statements for debugging
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo = echo

        # Sync engine and session
        self._sync_engine = None
        self._sync_session_factory = None

        # Async engine and session
        self._async_engine = None
        self._async_session_factory = None

    def _get_sync_url(self) -> str:
        """Get sync database URL (postgresql://)"""
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://")
        return url

    def _get_async_url(self) -> str:
        """Get async database URL (postgresql+asyncpg://)"""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        elif not url.startswith("postgresql+asyncpg://"):
            url = f"postgresql+asyncpg://{url.split('://', 1)[1]}"
        return url

    def init_sync_engine(self):
        """Initialize synchronous engine"""
        if self._sync_engine is None:
            self._sync_engine = create_engine(
                self._get_sync_url(),
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=self.echo
            )
            self._sync_session_factory = sessionmaker(
                bind=self._sync_engine,
                autocommit=False,
                autoflush=False
            )

            # Set up connection event listeners
            @event.listens_for(self._sync_engine, "connect")
            def set_search_path(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("SET search_path TO public")
                cursor.close()

    async def init_async_engine(self):
        """Initialize asynchronous engine"""
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                self._get_async_url(),
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=self.echo
            )
            self._async_session_factory = async_sessionmaker(
                bind=self._async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )

    def create_tables(self):
        """Create all tables (sync)"""
        self.init_sync_engine()
        Base.metadata.create_all(bind=self._sync_engine)
        logger.info("Database tables created successfully")

    async def create_tables_async(self):
        """Create all tables (async)"""
        await self.init_async_engine()
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully (async)")

    def drop_tables(self):
        """Drop all tables (sync) - USE WITH CAUTION"""
        self.init_sync_engine()
        Base.metadata.drop_all(bind=self._sync_engine)
        logger.warning("All database tables dropped")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a synchronous database session"""
        self.init_sync_engine()
        session = self._sync_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an asynchronous database session"""
        await self.init_async_engine()
        session = self._async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self):
        """Close all connections"""
        if self._async_engine:
            await self._async_engine.dispose()
            self._async_engine = None
            self._async_session_factory = None

        if self._sync_engine:
            self._sync_engine.dispose()
            self._sync_engine = None
            self._sync_session_factory = None

        logger.info("Database connections closed")

    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            await self.init_async_engine()
            async with self._async_engine.connect() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager(database_url: Optional[str] = None) -> DatabaseManager:
    """Get or create database manager instance"""
    global _db_manager

    if _db_manager is None:
        if database_url is None:
            from ..core.config import settings
            database_url = settings.database_url

        _db_manager = DatabaseManager(database_url)

    return _db_manager


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get a synchronous database session (convenience function)"""
    manager = get_database_manager()
    with manager.get_session() as session:
        yield session


@asynccontextmanager
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an asynchronous database session (convenience function)"""
    manager = get_database_manager()
    async with manager.get_async_session() as session:
        yield session


# FastAPI dependency for database sessions
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions"""
    manager = get_database_manager()
    async with manager.get_async_session() as session:
        yield session
