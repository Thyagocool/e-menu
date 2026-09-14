from httpx import AsyncClient

from tests.conftest import create_restaurant


async def test_create_restaurant(client: AsyncClient) -> None:
    payload = {
        "name": "Pizzaria Teste",
        "whatsapp_phone": "+5511999999999",
        "delivery_fee": "10.00",
        "status": "active",
    }
    response = await client.post("/restaurants", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "pizzaria-teste"
    assert data["whatsapp_phone"] == "+5511999999999"
    assert data["delivery_fee"] == "10.00"


async def test_create_restaurant_with_custom_slug(client: AsyncClient) -> None:
    response = await client.post("/restaurants", json={"name": "Bar do Zé", "slug": "bar-do-ze"})
    assert response.status_code == 201
    assert response.json()["slug"] == "bar-do-ze"


async def test_slug_must_be_unique(client: AsyncClient) -> None:
    await create_restaurant(client)
    response = await client.post("/restaurants", json={"name": "Pizzaria Teste 2", "slug": "pizzaria-teste"})
    assert response.status_code == 409


async def test_get_restaurant(client: AsyncClient) -> None:
    created = await create_restaurant(client)
    response = await client.get(f"/restaurants/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Pizzaria Teste"


async def test_get_restaurant_not_found(client: AsyncClient) -> None:
    assert (await client.get("/restaurants/9999")).status_code == 404


async def test_update_restaurant(client: AsyncClient) -> None:
    created = await create_restaurant(client)
    response = await client.put(f"/restaurants/{created['id']}", json={"name": "Pizzaria XYZ"})
    assert response.status_code == 200
    assert response.json()["name"] == "Pizzaria XYZ"


async def test_update_restaurant_slug_conflict(client: AsyncClient) -> None:
    await create_restaurant(client, slug="pizzaria-a")
    other = await create_restaurant(client, name="Outra", slug="outra")
    response = await client.put(f"/restaurants/{other['id']}", json={"slug": "pizzaria-a"})
    assert response.status_code == 409


async def test_validation_errors(client: AsyncClient) -> None:
    assert (await client.post("/restaurants", json={"name": ""})).status_code == 422
    assert (await client.post("/restaurants", json={"name": "X", "delivery_fee": "-1"})).status_code == 422