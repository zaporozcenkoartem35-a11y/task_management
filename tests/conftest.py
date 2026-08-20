import uuid
import pytest
from contextlib import asynccontextmanager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.api.deps import get_session
from main import app


@asynccontextmanager
async def mock_lifespan(app):
    yield


app.router.lifespan_context = mock_lifespan

test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
test_session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def get_test_session():
    async with test_session_maker() as session:
        yield session


app.dependency_overrides[get_session] = get_test_session


@pytest.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def auth_headers(ac: AsyncClient):
    uid = uuid.uuid4().hex[:6]
    user_payload = {
        "username": f"alex_{uid}",
        "password": "Password123"
    }
    await ac.post("/api/v1/auth/register", json=user_payload)
    login_res = await ac.post("/api/v1/auth/login", data={
        "username": user_payload["username"],
        "password": user_payload["password"]
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}