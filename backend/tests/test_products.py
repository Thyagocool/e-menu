from httpx import AsyncClient

from tests.conftest import create_category, create_restaurant


async def create_product(client: AsyncClient, restaurant_id: int, **overrides) -> dict:
    payload = {"name": "Pizza Calabresa", "base_price": "39.90", **overrides}
    response = await client.post(f"/restaurants/{restaurant_id}/products", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_product(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client)
    category = await create_category(client, restaurant["id"])
    product = await create_product(client, restaurant["id"], category_id=category["id"])
    assert product["category_id"] == category["id"]
    assert product["base_price"] == "39.90"


async def test_product_category_must_belong_to_restaurant(client: AsyncClient) -> None:
    r1 = await create_restaurant(client, name="Restaurante Um")
    r2 = await create_restaurant(client, name="Restaurante Dois")
    foreign_category = await create_category(client, r2["id"])
    response = await client.post(
        f"/restaurants/{r1['id']}/products",
        json={"name": "Pizza", "category_id": foreign_category["id"], "base_price": "10.00"},
    )
    assert response.status_code == 400


async def test_products_isolated_by_restaurant(client: AsyncClient) -> None:
    r1 = await create_restaurant(client, name="Restaurante Um")
    r2 = await create_restaurant(client, name="Restaurante Dois")
    await create_product(client, r1["id"])
    assert (await client.get(f"/restaurants/{r2['id']}/products")).json() == []


async def test_product_detail_includes_variants_and_addons(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client)
    product = await create_product(client, restaurant["id"])

    variant = await client.post(
        f"/products/{product['id']}/variants", json={"name": "Grande", "price": "49.90"}
    )
    assert variant.status_code == 201

    addon = await client.post(
        f"/restaurants/{restaurant['id']}/addons", json={"name": "Borda", "price": "8.00"}
    )
    attach = await client.post(f"/products/{product['id']}/addons", json={"addon_id": addon.json()["id"]})
    assert attach.status_code == 201

    detail = (await client.get(f"/products/{product['id']}")).json()
    assert [v["name"] for v in detail["variants"]] == ["Grande"]
    assert [a["name"] for a in detail["addons"]] == ["Borda"]


async def test_addon_must_belong_to_restaurant(client: AsyncClient) -> None:
    r1 = await create_restaurant(client, name="Restaurante Um")
    r2 = await create_restaurant(client, name="Restaurante Dois")
    product = await create_product(client, r1["id"])
    foreign_addon = await client.post(f"/restaurants/{r2['id']}/addons", json={"name": "X", "price": "1.00"})
    attach = await client.post(
        f"/products/{product['id']}/addons", json={"addon_id": foreign_addon.json()["id"]}
    )
    assert attach.status_code == 400


async def test_detach_addon(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client)
    product = await create_product(client, restaurant["id"])
    addon = (await client.post(
        f"/restaurants/{restaurant['id']}/addons", json={"name": "Borda", "price": "8.00"}
    )).json()
    await client.post(f"/products/{product['id']}/addons", json={"addon_id": addon["id"]})
    assert (await client.delete(f"/products/{product['id']}/addons/{addon['id']}")).status_code == 204
    assert (await client.get(f"/products/{product['id']}")).json()["addons"] == []


async def test_soft_delete_product(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client)
    product = await create_product(client, restaurant["id"])
    assert (await client.delete(f"/products/{product['id']}")).status_code == 204
    assert (await client.get(f"/products/{product['id']}")).status_code == 404
    assert (await client.get(f"/restaurants/{restaurant['id']}/products")).json() == []


async def test_update_product_status(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client)
    product = await create_product(client, restaurant["id"])
    response = await client.put(f"/products/{product['id']}", json={"status": "inactive"})
    assert response.status_code == 200
    assert response.json()["status"] == "inactive"


async def test_product_validation(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client)
    response = await client.post(
        f"/restaurants/{restaurant['id']}/products", json={"name": "Pizza", "base_price": "-1"}
    )
    assert response.status_code == 422