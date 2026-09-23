import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import get_db, get_redis
from app.db.base import Base

# Use a separate test database
TEST_DATABASE_URL = "postgresql+asyncpg://portalu:portalu@localhost:5432/portalu_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables at session start, drop at session end."""
    # Import all models so metadata is populated
    import app.db.models.org  # noqa: F401
    import app.db.models.rbac  # noqa: F401
    import app.db.models.user  # noqa: F401
    import app.db.models.request  # noqa: F401
    import app.db.models.portal  # noqa: F401
    import app.db.models.portal_request  # noqa: F401
    import app.db.models.citizen  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Truncate all tables between tests to ensure isolation."""
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
def mock_redis():
    """In-memory mock for Redis — avoids needing a real Redis in tests."""
    store = {}
    sets = {}

    redis = AsyncMock()

    async def set_val(key, value, ex=None):
        store[key] = value

    async def setex_val(key, ttl, value):
        store[key] = value

    async def get_val(key):
        return store.get(key)

    async def delete_val(*keys):
        for k in keys:
            store.pop(k, None)
            sets.pop(k, None)

    async def sadd_val(key, *values):
        sets.setdefault(key, set()).update(values)

    async def smembers_val(key):
        return sets.get(key, set())

    async def srem_val(key, *values):
        if key in sets:
            for v in values:
                sets[key].discard(v)

    async def exists_val(key):
        return key in store

    redis.set = set_val
    redis.setex = setex_val
    redis.get = get_val
    redis.delete = delete_val
    redis.sadd = sadd_val
    redis.smembers = smembers_val
    redis.srem = srem_val
    redis.exists = exists_val

    return redis


@pytest_asyncio.fixture
async def client(mock_redis):
    """Async test client with DB and Redis overrides."""
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    async def override_get_redis():
        yield mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Helper fixtures ───────────────────────────────────────────

@pytest_asyncio.fixture
async def registered_org(client):
    """Creates an org + super admin user, returns {access_token, refresh_token, user}."""
    res = await client.post("/api/v1/auth/sign-up", json={
        "email": "admin@prefeitura.gov.br",
        "password": "adminpass123",
        "name": "Admin",
        "org_name": "Prefeitura Municipal"
    })
    assert res.status_code == 201
    verification_token = res.json()["verification_token"]

    res = await client.post("/api/v1/auth/verify-email", json={"token": verification_token})
    assert res.status_code == 200
    return res.json()


@pytest_asyncio.fixture
async def auth_headers(registered_org):
    """Returns Authorization headers for the super admin."""
    return {"Authorization": f"Bearer {registered_org['access_token']}"}
