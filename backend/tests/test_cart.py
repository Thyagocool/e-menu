from httpx import AsyncClient

from tests.conftest import create_restaurant
from tests.test_whatsapp import meta_payload


async def create_product(client: AsyncClient, restaurant_id: int, **overrides) -> dict:
    payload = {"name": "Pizza Calabresa", "base_price": "39.90", **overrides}
    response = await client.post(f"/restaurants/{restaurant_id}/products", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def create_addon(
    client: AsyncClient, restaurant_id: int, product_id: int | None = None, **overrides
) -> dict:
    addon = (
        await client.post(
            f"/restaurants/{restaurant_id}/addons", json={"name": "Borda", "price": "8.00", **overrides}
        )
    ).json()
    if product_id is not None:
        await client.post(f"/products/{product_id}/addons", json={"addon_id": addon["id"]})
    return addon


async def setup(client: AsyncClient, **overrides) -> tuple[int, int]:
    """Cria restaurante + customer via webhook; retorna (customer_id, restaurant_id)."""
    restaurant = await create_restaurant(
        client, name="Pizzaria Sol", slug="pizzaria-sol", whatsapp_phone="5511999991234"
    )
    response = await client.post("/webhooks/whatsapp", json=meta_payload(**overrides))
    assert response.status_code == 200, response.text
    return response.json()["customer_id"], restaurant["id"]


async def test_add_basic_product(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id, base_price="10.00")

    body = (
        await client.post(
            "/cart/items",
            json={"customer_id": customer_id, "product_id": product["id"], "quantity": 2},
        )
    ).json()
    assert body["subtotal"] == "20.00"
    assert body["items"][0]["unit_price"] == "10.00"
    assert body["items"][0]["line_total"] == "20.00"


async def test_add_with_variant(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id, base_price="10.00")
    variant = (
        await client.post(f"/products/{product['id']}/variants", json={"name": "Grande", "price": "49.90"})
    ).json()

    body = (
        await client.post(
            "/cart/items",
            json={
                "customer_id": customer_id,
                "product_id": product["id"],
                "variant_id": variant["id"],
                "quantity": 1,
            },
        )
    ).json()
    assert body["items"][0]["unit_price"] == "49.90"
    assert body["items"][0]["variant_name"] == "Grande"
    assert body["subtotal"] == "49.90"


async def test_add_with_addons_uses_snapshot_prices(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id, base_price="30.00")
    addon1 = await create_addon(client, restaurant_id, product["id"], name="Borda", price="8.00")
    addon2 = await create_addon(client, restaurant_id, product["id"], name="Extra queijo", price="5.00")

    body = (
        await client.post(
            "/cart/items",
            json={
                "customer_id": customer_id,
                "product_id": product["id"],
                "quantity": 1,
                "addon_ids": [addon1["id"], addon2["id"]],
            },
        )
    ).json()
    item = body["items"][0]
    assert {a["name"]: a["price"] for a in item["addons"]} == {"Borda": "8.00", "Extra queijo": "5.00"}
    assert item["line_total"] == "43.00"  # 30 + 8 + 5
    assert body["subtotal"] == "43.00"


async def test_add_same_item_increments_quantity(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id, base_price="10.00")

    await client.post(
        "/cart/items", json={"customer_id": customer_id, "product_id": product["id"], "quantity": 2}
    )
    body = (
        await client.post(
            "/cart/items", json={"customer_id": customer_id, "product_id": product["id"], "quantity": 3}
        )
    ).json()
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 5
    assert body["subtotal"] == "50.00"


async def test_add_same_product_different_addons_are_separate_items(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id, base_price="10.00")
    addon = await create_addon(client, restaurant_id, product["id"])

    await client.post(
        "/cart/items", json={"customer_id": customer_id, "product_id": product["id"], "quantity": 1}
    )
    body = (
        await client.post(
            "/cart/items",
            json={
                "customer_id": customer_id,
                "product_id": product["id"],
                "quantity": 1,
                "addon_ids": [addon["id"]],
            },
        )
    ).json()
    assert len(body["items"]) == 2
    assert body["subtotal"] == "28.00"  # 10 + (10+8)


async def test_subtotal_multiple_items_strong_calculation(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    plain = await create_product(client, restaurant_id, name="Refrigerante", base_price="6.00")
    pizzeria = await create_product(client, restaurant_id, name="Pizza", base_price="30.00")
    variant = (
        await client.post(f"/products/{pizzeria['id']}/variants", json={"name": "Grande", "price": "45.00"})
    ).json()
    addon = await create_addon(client, restaurant_id, pizzeria["id"], name="Borda", price="8.00")

    await client.post(
        "/cart/items", json={"customer_id": customer_id, "product_id": plain["id"], "quantity": 2}
    )  # 12.00
    await client.post(
        "/cart/items",
        json={
            "customer_id": customer_id,
            "product_id": pizzeria["id"],
            "variant_id": variant["id"],
            "quantity": 3,
            "addon_ids": [addon["id"]],
        },
    )  # (45 + 8) * 3 = 159.00

    body = (await client.get(f"/customers/{customer_id}/cart")).json()
    assert len(body["items"]) == 2
    assert body["subtotal"] == "171.00"  # 12.00 + 159.00
    assert body["items"][1]["line_total"] == "159.00"


async def test_update_quantity(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id, base_price="10.00")
    item_id = (
        await client.post(
            "/cart/items", json={"customer_id": customer_id, "product_id": product["id"], "quantity": 1}
        )
    ).json()["items"][0]["id"]

    body = (await client.put(f"/cart/items/{item_id}", json={"quantity": 4})).json()
    assert body["items"][0]["quantity"] == 4
    assert body["subtotal"] == "40.00"


async def test_remove_item(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    p1 = await create_product(client, restaurant_id, name="A", base_price="10.00")
    p2 = await create_product(client, restaurant_id, name="B", base_price="20.00")
    await client.post(
        "/cart/items", json={"customer_id": customer_id, "product_id": p1["id"], "quantity": 1}
    )
    created = await client.post(
        "/cart/items", json={"customer_id": customer_id, "product_id": p2["id"], "quantity": 1}
    )
    item_id = created.json()["items"][1]["id"]

    body = (await client.delete(f"/cart/items/{item_id}")).json()
    assert len(body["items"]) == 1
    assert body["items"][0]["product_name"] == "A"
    assert body["subtotal"] == "10.00"
    assert (await client.delete(f"/cart/items/{item_id}")).status_code == 404


async def test_clear_cart(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id)
    await client.post(
        "/cart/items", json={"customer_id": customer_id, "product_id": product["id"], "quantity": 2}
    )
    body = (await client.delete(f"/customers/{customer_id}/cart")).json()
    assert body["items"] == []
    assert body["subtotal"] == "0.00"


async def test_inactive_product_rejected(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id)
    await client.put(f"/products/{product['id']}", json={"status": "inactive"})
    response = await client.post(
        "/cart/items", json={"customer_id": customer_id, "product_id": product["id"], "quantity": 1}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Produto indisponível"


async def test_inactive_variant_rejected(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id)
    variant = (
        await client.post(
            f"/products/{product['id']}/variants", json={"name": "P", "price": "20.00", "status": "inactive"}
        )
    ).json()
    response = await client.post(
        "/cart/items",
        json={
            "customer_id": customer_id,
            "product_id": product["id"],
            "variant_id": variant["id"],
            "quantity": 1,
        },
    )
    assert response.status_code == 400


async def test_variant_required_when_product_has_variants(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id)
    await client.post(f"/products/{product['id']}/variants", json={"name": "Grande", "price": "49.90"})
    response = await client.post(
        "/cart/items", json={"customer_id": customer_id, "product_id": product["id"], "quantity": 1}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Selecione uma variação"


async def test_addon_not_linked_to_product_rejected(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id)
    addon = await create_addon(client, restaurant_id)  # existe, mas não vinculado ao produto
    response = await client.post(
        "/cart/items",
        json={
            "customer_id": customer_id,
            "product_id": product["id"],
            "quantity": 1,
            "addon_ids": [addon["id"]],
        },
    )
    assert response.status_code == 400


async def test_addon_from_other_restaurant_rejected(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    other = await create_restaurant(client, name="Outra", slug="outra")
    product = await create_product(client, restaurant_id)
    foreign_addon = await create_addon(client, other["id"])

    response = await client.post(
        "/cart/items",
        json={
            "customer_id": customer_id,
            "product_id": product["id"],
            "quantity": 1,
            "addon_ids": [foreign_addon["id"]],
        },
    )
    assert response.status_code == 400


async def test_unknown_customer_404(client: AsyncClient) -> None:
    assert (await client.get("/customers/999/cart")).status_code == 404
    response = await client.post(
        "/cart/items", json={"customer_id": 999, "product_id": 1, "quantity": 1}
    )
    assert response.status_code == 404


async def test_quantity_zero_rejected(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id)
    assert (
        await client.post(
            "/cart/items", json={"customer_id": customer_id, "product_id": product["id"], "quantity": 0}
        )
    ).status_code == 422


async def test_carts_are_isolated_per_customer(client: AsyncClient) -> None:
    customer_a, restaurant_id = await setup(client, customer="5511987654321")
    customer_b = (
        await client.post(
            "/webhooks/whatsapp", json=meta_payload(customer="5511988881111", msg_id="wamid-2")
        )
    ).json()["customer_id"]
    product = await create_product(client, restaurant_id, base_price="10.00")

    await client.post(
        "/cart/items", json={"customer_id": customer_a, "product_id": product["id"], "quantity": 1}
    )
    cart_a = (await client.get(f"/customers/{customer_a}/cart")).json()
    cart_b = (await client.get(f"/customers/{customer_b}/cart")).json()
    assert len(cart_a["items"]) == 1
    assert cart_b["items"] == []
    assert cart_b["subtotal"] == "0.00"