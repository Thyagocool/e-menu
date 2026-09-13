from httpx import AsyncClient

from tests.conftest import create_category, create_restaurant


async def create_product(client: AsyncClient, restaurant_id: int, **overrides) -> dict:
    payload = {"name": "Pizza Calabresa", "base_price": "39.90", **overrides}
    response = await client.post(f"/restaurants/{restaurant_id}/products", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def test_public_menu_with_categories_and_products(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client, name="Pizzaria Sol", slug="pizzaria-sol")
    category = await create_category(client, restaurant["id"])
    product = await create_product(client, restaurant["id"], category_id=category["id"])

    await client.post(
        f"/products/{product['id']}/variants", json={"name": "Grande", "price": "49.90"}
    )
    addon = (await client.post(
        f"/restaurants/{restaurant['id']}/addons", json={"name": "Borda", "price": "8.00"}
    )).json()
    await client.post(f"/products/{product['id']}/addons", json={"addon_id": addon["id"]})

    response = await client.get("/public/restaurants/pizzaria-sol/menu")
    assert response.status_code == 200
    body = response.json()
    assert body["restaurant"]["name"] == "Pizzaria Sol"
    assert body["categories"][0]["name"] == "Pizzas"
    product_public = body["categories"][0]["products"][0]
    assert product_public["name"] == "Pizza Calabresa"
    assert [v["name"] for v in product_public["variants"]] == ["Grande"]
    assert [a["name"] for a in product_public["addons"]] == ["Borda"]


async def test_public_menu_uncategorized_products(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client, name="Bar do Zé", slug="bar-do-ze")
    await create_product(client, restaurant["id"])
    body = (await client.get("/public/restaurants/bar-do-ze/menu")).json()
    assert len(body["uncategorized_products"]) == 1
    assert body["categories"] == []


async def test_public_menu_hides_inactive_restaurant(client: AsyncClient) -> None:
    await create_restaurant(client, name="Fechada", slug="fechada", status="inactive")
    response = await client.get("/public/restaurants/fechada/menu")
    assert response.status_code == 404


async def test_public_menu_unknown_slug(client: AsyncClient) -> None:
    assert (await client.get("/public/restaurants/nao-existe/menu")).status_code == 404


async def test_public_menu_hides_inactive_product_and_variants(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client, name="Café Bom", slug="cafe-bom")
    product = await create_product(client, restaurant["id"])
    await client.put(f"/products/{product['id']}", json={"status": "inactive"})
    body = (await client.get("/public/restaurants/cafe-bom/menu")).json()
    assert body["uncategorized_products"] == []

    active = await create_product(client, restaurant["id"], name="Café")
    inactive_variant = await client.post(
        f"/products/{active['id']}/variants", json={"name": "2x", "price": "12.00", "status": "inactive"}
    )
    assert inactive_variant.status_code == 201
    await client.post(
        f"/products/{active['id']}/variants", json={"name": "300ml", "price": "9.00"}
    )
    menu_body = (await client.get("/public/restaurants/cafe-bom/menu")).json()
    menu_product = menu_body["uncategorized_products"][0]
    assert menu_product["name"] == "Café"
    assert [v["name"] for v in menu_product["variants"]] == ["300ml"]


async def test_public_product_detail(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client, name="Pizzaria Sol", slug="pizzaria-sol")
    product = await create_product(client, restaurant["id"])
    response = await client.get(f"/public/restaurants/pizzaria-sol/products/{product['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Pizza Calabresa"


async def test_public_product_not_found_for_other_restaurant(client: AsyncClient) -> None:
    r1 = await create_restaurant(client, name="Um", slug="um")
    await create_restaurant(client, name="Dois", slug="dois")
    product = await create_product(client, r1["id"])
    assert (await client.get(f"/public/restaurants/dois/products/{product['id']}")).status_code == 404
    assert (await client.get(f"/public/restaurants/um/products/{product['id']}")).status_code == 200


async def test_public_inactive_product_detail_404(client: AsyncClient) -> None:
    restaurant = await create_restaurant(client, name="Café Bom", slug="cafe-bom")
    product = await create_product(client, restaurant["id"])
    await client.put(f"/products/{product['id']}", json={"status": "inactive"})
    assert (await client.get(f"/public/restaurants/cafe-bom/products/{product['id']}")).status_code == 404