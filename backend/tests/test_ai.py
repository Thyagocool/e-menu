from httpx import AsyncClient

from tests.conftest import create_restaurant
from tests.test_whatsapp import meta_payload


async def send(client: AsyncClient, text: str, msg_id: str = "wamid-ai-1") -> dict:
    """Envia mensagem do cliente via webhook e retorna a resposta do garçom."""
    response = await client.post(
        "/webhooks/whatsapp", json=meta_payload(msg_id=msg_id, text=text)
    )
    assert response.status_code == 200, response.text
    return response.json()


async def setup_restaurant(client: AsyncClient) -> int:
    restaurant = await create_restaurant(
        client,
        name="Pizzaria Sol",
        slug="pizzaria-sol",
        whatsapp_phone="5511999991234",
        description="Pizzaria artesanal, massa fina e forno a lenha.",
        opening_hours="18h às 23h",
        delivery_fee="10.00",
    )
    product = await client.post(
        f"/restaurants/{restaurant['id']}/products",
        json={"name": "Pizza Calabresa", "base_price": "39.90"},
    )
    drinks = await client.post(
        f"/restaurants/{restaurant['id']}/products", json={"name": "Coca 2L", "base_price": "12.00"}
    )
    variant = await client.post(
        f"/products/{product.json()['id']}/variants", json={"name": "Grande", "price": "49.90"}
    )
    await client.post(
        f"/products/{product.json()['id']}/variants", json={"name": "Média", "price": "39.90"}
    )
    await client.post(f"/products/{drinks.json()['id']}/variants", json={"name": "Gelada", "price": "12.00"})
    return restaurant["id"], product.json()["id"], drinks.json()["id"], variant.json()["id"]


async def test_assistant_greets(client: AsyncClient) -> None:
    await setup_restaurant(client)
    body = await send(client, "Oi")
    assert "Olá" in body["reply"]


async def test_assistant_lists_menu(client: AsyncClient) -> None:
    await setup_restaurant(client)
    body = await send(client, "Quero ver o cardápio")
    assert "Pizza Calabresa" in body["reply"]
    assert "Coca 2L" in body["reply"]


async def test_assistant_searches_product(client: AsyncClient) -> None:
    await setup_restaurant(client)
    body = await send(client, "tem coca?")
    assert "Coca 2L" in body["reply"]
    assert "Pizza" not in body["reply"]


async def test_assistant_adds_product_with_quantity(client: AsyncClient) -> None:
    _, product_id, _, _ = await setup_restaurant(client)
    # produto com variações: o assistente escolhe a primeira variação ativa (Grande)
    body = await send(client, "quero 2 pizzas", msg_id="wamid-ai-2")
    assert "Pizza Calabresa" in body["reply"]
    customer_id = body["customer_id"]
    cart = (await client.get(f"/customers/{customer_id}/cart")).json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 2
    assert cart["items"][0]["variant_name"] == "Grande"
    assert cart["subtotal"] == "99.80"  # 49.90 × 2


async def test_assistant_adds_increments_quantity_for_same_item(client: AsyncClient) -> None:
    _, product_id, _, _ = await setup_restaurant(client)
    body = await send(client, "quero 2 pizzas", msg_id="wamid-ai-3")
    customer_id = body["customer_id"]
    await send(client, "adiciona 1 pizza", msg_id="wamid-ai-4")
    cart = (await client.get(f"/customers/{customer_id}/cart")).json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 3


async def test_assistant_updates_quantity(client: AsyncClient) -> None:
    await setup_restaurant(client)
    body = await send(client, "quero 2 pizzas", msg_id="wamid-ai-5")
    customer_id = body["customer_id"]
    reply = await send(client, "coloca mais uma pizza", msg_id="wamid-ai-6")
    assert "3x" in reply["reply"]
    cart = (await client.get(f"/customers/{customer_id}/cart")).json()
    assert cart["items"][0]["quantity"] == 3


async def test_assistant_updates_first_item_without_name(client: AsyncClient) -> None:
    await setup_restaurant(client)
    body = await send(client, "quero 1 pizza e 1 coca", msg_id="wamid-ai-14")
    customer_id = body["customer_id"]
    reply = await send(client, "coloca mais uma", msg_id="wamid-ai-15")
    assert "2x" in reply["reply"]
    assert "1x" in reply["reply"]  # coca seguiu com 1
    cart = (await client.get(f"/customers/{customer_id}/cart")).json()
    pizza = next(i for i in cart["items"] if i["product_name"] == "Pizza Calabresa")
    assert pizza["quantity"] == 2


async def test_assistant_removes_item(client: AsyncClient) -> None:
    await setup_restaurant(client)
    body = await send(client, "quero 2 pizzas e 1 coca", msg_id="wamid-ai-7")
    customer_id = body["customer_id"]
    reply = await send(client, "tira a coca", msg_id="wamid-ai-8")
    cart = (await client.get(f"/customers/{customer_id}/cart")).json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_name"] == "Pizza Calabresa"
    assert "Pizza Calabresa" in reply["reply"]


async def test_assistant_shows_cart(client: AsyncClient) -> None:
    await setup_restaurant(client)
    await send(client, "quero 1 pizza", msg_id="wamid-ai-9")
    reply = await send(client, "meu pedido", msg_id="wamid-ai-10")
    assert "49.90" in reply["reply"]
    assert "Seu pedido" in reply["reply"]


async def test_assistant_empty_cart_message(client: AsyncClient) -> None:
    await setup_restaurant(client)
    await send(client, "oi", msg_id="wamid-ai-11")
    body = await send(client, "meu pedido", msg_id="wamid-ai-12")
    assert "vazio" in body["reply"]


async def test_assistant_unknown_product_responds_nicely(client: AsyncClient) -> None:
    await setup_restaurant(client)
    body = await send(client, "quero um X-Burger", msg_id="wamid-ai-13")
    assert "X-Burger" not in body["reply"]


async def test_assistant_removing_item_not_in_cart_keeps_cart(client: AsyncClient) -> None:
    await setup_restaurant(client)
    body = await send(client, "quero 1 pizza", msg_id="wamid-ai-16")
    customer_id = body["customer_id"]
    reply = await send(client, "tira a coca", msg_id="wamid-ai-17")
    assert "Item não encontrado" in reply["reply"]
    cart = (await client.get(f"/customers/{customer_id}/cart")).json()
    assert len(cart["items"]) == 1  # pizza seguiu no carrinho


async def test_assistant_knows_restaurant_info(client: AsyncClient) -> None:
    restaurant_id, _, _, _ = await setup_restaurant(client)
    from src.infra.database import SessionLocal
    from src.modules.ai.tools import ToolRegistry

    async with SessionLocal() as session:
        result = await ToolRegistry().execute(
            session, "get_restaurant_info", restaurant_id=restaurant_id
        )
    assert result["name"] == "Pizzaria Sol"
    assert "forno a lenha" in result["resumo"]
    assert result["delivery_fee"] == "10.00"