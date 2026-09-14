from httpx import AsyncClient

from tests.conftest import create_category, create_restaurant


async def test_create_category(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client)
    response = await client.post(
        f"/restaurants/{restaurant['id']}/categories", json={"name": "Pizzas", "sort_order": 1}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Pizzas"
    assert data["restaurant_id"] == restaurant["id"]


async def test_list_categories_ordered(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client)
    await create_category(client, restaurant["id"], name="Bebidas", sort_order=2)
    await create_category(client, restaurant["id"], name="Pizzas", sort_order=1)
    response = await client.get(f"/restaurants/{restaurant['id']}/categories")
    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert names == ["Pizzas", "Bebidas"]


async def test_categories_isolated_by_restaurant(client: AsyncClient) -> None:
    r1 = await create_restaurant(client, name="Restaurante Um")
    r2 = await create_restaurant(client, name="Restaurante Dois")
    await create_category(client, r1["id"], name="Só do Um")
    response = await client.get(f"/restaurants/{r2['id']}/categories")
    assert response.json() == []


async def test_update_category(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client)
    category = await create_category(client, restaurant["id"])
    payload = {"name": "Massas", "status": "inactive"}
    response = await client.put(f"/categories/{category['id']}", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Massas"
    assert response.json()["status"] == "inactive"


async def test_soft_delete_category(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client)
    category = await create_category(client, restaurant["id"])
    assert (await client.delete(f"/categories/{category['id']}")).status_code == 204
    assert (await client.get(f"/restaurants/{restaurant['id']}/categories")).json() == []
    assert (await client.put(f"/categories/{category['id']}", json={"name": "X"})).status_code == 404


async def test_delete_category_with_products_conflicts(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client)
    category = await create_category(client, restaurant["id"])
    await client.post(
        f"/restaurants/{restaurant['id']}/products",
        json={"name": "Pizza", "category_id": category["id"], "base_price": "30.00"},
    )
    assert (await client.delete(f"/categories/{category['id']}")).status_code == 409