from httpx import AsyncClient

from tests.test_cart import create_product
from tests.test_order import add_item, checkout, setup


async def place_order(client: AsyncClient, customer_id: int, restaurant_id: int) -> dict:
    product = await create_product(client, restaurant_id, base_price="25.00")
    await add_item(client, customer_id, product["id"], 1)
    return await checkout(client, customer_id)


async def test_dashboard_metricas_do_dia(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    await place_order(client, customer_id, restaurant_id)
    done = await place_order(client, customer_id, restaurant_id)
    await place_order(client, customer_id, restaurant_id)
    await client.put(f"/orders/{done['id']}/status", json={"status": "COMPLETED"})

    response = await client.get(f"/restaurants/{restaurant_id}/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["orders_today"] == 3
    assert body["revenue_today"] == "25.00"  # só pedido COMPLETED conta
    assert body["pending_orders"] == 2  # RECEIVED + RECEIVED


async def test_dashboard_cancelado_nao_conta(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    cancelled = await place_order(client, customer_id, restaurant_id)
    await client.put(f"/orders/{cancelled['id']}/status", json={"status": "CANCELLED"})

    body = (await client.get(f"/restaurants/{restaurant_id}/dashboard")).json()
    assert body["orders_today"] == 1
    assert body["revenue_today"] == "0.00"
    assert body["pending_orders"] == 0


async def test_dashboard_top_produtos(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    pizza = await create_product(client, restaurant_id, base_price="40.00")
    coca = await create_product(client, restaurant_id, name="Coca-Cola", base_price="8.00")
    await add_item(client, customer_id, pizza["id"], 2)
    await add_item(client, customer_id, coca["id"], 3)
    await checkout(client, customer_id)

    body = (await client.get(f"/restaurants/{restaurant_id}/dashboard")).json()
    top = body["top_products"]
    assert top[0]["name"] == "Coca-Cola"  # maior quantidade primeiro
    assert top[0]["quantity"] == 3
    assert top[0]["revenue"] == "24.00"
    assert top[1]["name"] == "Pizza Calabresa"
    assert top[1]["quantity"] == 2
    assert top[1]["revenue"] == "80.00"


async def test_dashboard_restaurante_inexistente_404(client: AsyncClient) -> None:
    assert (await client.get("/restaurants/9999/dashboard")).status_code == 404


async def test_qr_code_cardapio(client: AsyncClient) -> None:
    _, restaurant_id = await setup(client)

    response = await client.get(f"/restaurants/{restaurant_id}/qr")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert b"<svg" in response.content