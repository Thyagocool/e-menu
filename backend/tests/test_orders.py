from httpx import AsyncClient

from src.modules.order.models import Order
from tests.test_cart import create_product
from tests.test_order import add_item, checkout, setup
from tests.test_whatsapp import count_rows


async def place_order(client: AsyncClient, customer_id: int, restaurant_id: int) -> dict:
    product = await create_product(client, restaurant_id, base_price="25.00")
    await add_item(client, customer_id, product["id"], 1)
    return await checkout(client, customer_id)


async def test_listar_pedidos_do_restaurante(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    first = await place_order(client, customer_id, restaurant_id)
    second = await place_order(client, customer_id, restaurant_id)

    response = await client.get(f"/restaurants/{restaurant_id}/orders")
    assert response.status_code == 200
    orders = response.json()
    assert [o["id"] for o in orders] == [second["id"], first["id"]]  # mais recente primeiro
    for o in orders:
        assert o["customer_name"] == "Maria"
        assert o["total"] == "25.00"
        assert o["status"] == "RECEIVED"
        assert o["items"][0]["product_name"] == "Pizza Calabresa"


async def test_listar_orders_filtra_por_status(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    await place_order(client, customer_id, restaurant_id)
    done = await place_order(client, customer_id, restaurant_id)
    await client.put(f"/orders/{done['id']}/status", json={"status": "COMPLETED"})

    response = await client.get(f"/restaurants/{restaurant_id}/orders", params={"status": "COMPLETED"})
    assert [o["id"] for o in response.json()] == [done["id"]]


async def test_get_order_mostra_detalhe_com_snapshot(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id, base_price="20.00")
    variant = (
        await client.post(f"/products/{product['id']}/variants", json={"name": "Grande", "price": "49.90"})
    ).json()
    await client.post(
        "/cart/items",
        json={
            "customer_id": customer_id,
            "product_id": product["id"],
            "variant_id": variant["id"],
            "quantity": 2,
        },
    )
    order = await checkout(
        client, customer_id, delivery_type="entrega", address="Rua das Flores 123", payment_method="dinheiro"
    )

    response = await client.get(f"/orders/{order['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["product_name"] == "Pizza Calabresa"
    assert body["items"][0]["variant_name"] == "Grande"
    assert body["items"][0]["unit_price"] == "49.90"
    assert body["address"] == "Rua das Flores 123"
    assert body["customer_name"] == "Maria"


async def test_atualizar_status_pedido(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    order = await place_order(client, customer_id, restaurant_id)

    response = await client.put(f"/orders/{order['id']}/status", json={"status": "CONFIRMED"})
    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"

    for status in ("PREPARING", "READY", "DELIVERING", "COMPLETED"):
        response = await client.put(f"/orders/{order['id']}/status", json={"status": status})
        assert response.json()["status"] == status
    assert await count_rows(Order, id=order["id"], status="COMPLETED") == 1


async def test_status_invalido_rejeitado(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    order = await place_order(client, customer_id, restaurant_id)

    response = await client.put(f"/orders/{order['id']}/status", json={"status": "CANCELADO"})
    assert response.status_code == 422
    assert await count_rows(Order, id=order["id"], status="RECEIVED") == 1


async def test_pedido_inexistente_404(client: AsyncClient) -> None:
    assert (await client.get("/orders/9999")).status_code == 404
    assert (await client.put("/orders/9999/status", json={"status": "CANCELLED"})).status_code == 404


async def test_listar_orders_isolado_por_restaurante(client: AsyncClient) -> None:
    _, restaurant_a = await setup(
        client, name="Pizzaria A", slug="pizzaria-a", whatsapp_phone="5511999991001"
    )
    customer_b, restaurant_b = await setup(
        client, msg_id="wamid-2", name="Pizzaria B", slug="pizzaria-b", whatsapp_phone="5511999991002"
    )
    await place_order(client, customer_b, restaurant_b)

    # restaurante A não vê pedidos de B
    assert (await client.get(f"/restaurants/{restaurant_a}/orders")).json() == []
    assert len((await client.get(f"/restaurants/{restaurant_b}/orders")).json()) == 1