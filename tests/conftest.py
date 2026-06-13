import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///./test_jobtracker.db",
)

connect_args = {"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}

if "sqlite" in TEST_DATABASE_URL:
    engine_test = create_async_engine(TEST_DATABASE_URL, connect_args=connect_args, echo=False)
else:
    engine_test = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
TestSessionLocal = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def setup_tables():
    async def create():
        async with engine_test.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop():
        async with engine_test.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine_test.dispose()

    asyncio.run(create())
    yield
    asyncio.run(drop())


@pytest_asyncio.fixture(autouse=True)
async def clear_tables():
    yield
    try:
        async with engine_test.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(table.delete())
    except Exception:
        pass


@pytest_asyncio.fixture
async def db():
    async with TestSessionLocal() as session:
        yield session
        try:
            await session.rollback()
        except Exception:
            pass


@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client):
    await client.post("/auth/register", json={
        "email": "testuser@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    })
    response = await client.post("/auth/login", data={
        "username": "testuser@example.com",
        "password": "testpassword123",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def second_auth_headers(client):
    await client.post("/auth/register", json={
        "email": "seconduser@example.com",
        "password": "testpassword123",
        "full_name": "Second User",
    })
    response = await client.post("/auth/login", data={
        "username": "seconduser@example.com",
        "password": "testpassword123",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def demo_auth_headers(client, db):
    await client.post("/auth/register", json={
        "email": "demo@example.com",
        "password": "demopassword123",
        "full_name": "Demo User",
    })
    user = (await db.execute(select(User).where(User.email == "demo@example.com"))).scalar_one()
    user.role = UserRole.DEMO
    await db.commit()

    response = await client.post("/auth/login", data={
        "username": "demo@example.com",
        "password": "demopassword123",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
