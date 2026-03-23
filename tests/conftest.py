import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fraud_engine.adapters.cache.redis_cache import RedisCache
from fraud_engine.adapters.events.in_memory_bus import InMemoryEventBus
from fraud_engine.adapters.persistence.orm import Base
from fraud_engine.config import settings


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.fixture
async def async_client(db_engine, event_bus) -> AsyncGenerator[AsyncClient, None]:
    from fraud_engine.adapters.persistence.database import get_session
    from fraud_engine.adapters.storage.s3_client import S3StorageClient
    from fraud_engine.main import create_app

    app = create_app()

    # Override session dependency
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_session():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = override_session

    # Set up app state
    cache = RedisCache(settings.redis_url)
    storage = S3StorageClient(settings)
    app.state.cache = cache
    app.state.event_bus = event_bus
    app.state.storage = storage

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await cache.close()
