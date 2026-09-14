import os

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://e_menu:e_menu@localhost:5434/e_menu_test"),
)

import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from alembic import command  # noqa: E402
from src.infra.database import Base, engine  # noqa: E402
from src.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def run_migrations() -> None:
    command.upgrade(Config("alembic.ini"), "head")
    yield


@pytest.fixture(autouse=True)
async def clean_tables() -> None:
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    await engine.dispose()


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def create_restaurant(client: AsyncClient, name: str = "Pizzaria Teste", **overrides) -> dict:
    payload = {"name": name, "slug": None, "delivery_fee": "10.00", **overrides}
    response = await client.post("/restaurants", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def create_category(client: AsyncClient, restaurant_id: int, name: str = "Pizzas", **overrides) -> dict:
    response = await client.post(f"/restaurants/{restaurant_id}/categories", json={"name": name, **overrides})
    assert response.status_code == 201, response.text
    return response.json()