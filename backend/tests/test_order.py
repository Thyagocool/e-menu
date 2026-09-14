from httpx import AsyncClient

from src.modules.order.models import Order
from tests.conftest import create_restaurant
from tests.test_cart import create_product
from tests.test_whatsapp import count_rows, meta_payload


async def setup(client: AsyncClient, msg_id: str = "wamid-1", **restaurant_kwargs) -> tuple[int, int]:
    """Restaurante (delivery_fee configurável) + customer via webhook."""
    defaults = {"name": "Pizzaria Sol", "slug": "pizzaria-sol", "whatsapp_phone": "5511999991234"}
    kwargs = {**defaults, **restaurant_kwargs}
    restaurant = await create_restaurant(client, **kwargs)
    response = await client.post(
        "/webhooks/whatsapp", json=meta_payload(msg_id=msg_id, restaurant=kwargs["whatsapp_phone"])
    )
    assert response.status_code == 200, response.text
    return response.json()["customer_id"], restaurant["id"]


async def checkout(client: AsyncClient, customer_id: int, **overrides) -> dict:
    payload = {"delivery_type": "retirada", "payment_method": "pix", **overrides}
    response = await client.post(f"/customers/{customer_id}/checkout", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def preview(client: AsyncClient, customer_id: int, **overrides) -> dict:
    payload = {"delivery_type": "retirada", **overrides}
    response = await client.post(f"/customers/{customer_id}/checkout/preview", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


async def add_item(client: AsyncClient, customer_id: int, product_id: int, quantity: int = 1) -> None:
    response = await client.post(
        "/cart/items",
        json={"customer_id": customer_id, "product_id": product_id, "quantity": quantity},
    )
    assert response.status_code == 201, response.text


async def test_preview_retirada_sem_taxa(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client, delivery_fee="10.00")
    product = await create_product(client, restaurant_id, base_price="20.00")
    await add_item(client, customer_id, product["id"], 2)

    body = await preview(client, customer_id)
    assert body["delivery_type"] == "retirada"
    assert body["subtotal"] == "40.00"
    assert body["delivery_fee"] == "0.00"
    assert body["total"] == "40.00"
    assert body["items"][0]["quantity"] == 2


async def test_preview_entrega_soma_taxa_fixa(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client, delivery_fee="10.00")
    product = await create_product(client, restaurant_id, base_price="20.00")
    await add_item(client, customer_id, product["id"], 2)

    body = await preview(client, customer_id, delivery_type="entrega")
    assert body["delivery_fee"] == "10.00"
    assert body["total"] == "50.00"


async def test_preview_carrinho_vazio_falha(client: AsyncClient) -> None:
    customer_id, _ = await setup(client)
    response = await client.post(
        f"/customers/{customer_id}/checkout/preview", json={"delivery_type": "retirada"}
    )
    assert response.status_code == 400
    assert "vazio" in response.json()["detail"]


async def test_create_snapshot_e_limpa_carrinho(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client, delivery_fee="10.00")
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

    body = await checkout(client, customer_id)
    assert body["status"] == "RECEIVED"
    assert body["delivery_type"] == "retirada"
    assert body["payment_method"] == "pix"
    assert body["subtotal"] == "99.80"
    assert body["total"] == "99.80"
    assert body["items"][0]["product_name"] == "Pizza Calabresa"
    assert body["items"][0]["variant_name"] == "Grande"
    assert body["items"][0]["unit_price"] == "49.90"
    assert body["items"][0]["line_total"] == "99.80"

    cart = (await client.get(f"/customers/{customer_id}/cart")).json()
    assert cart["items"] == []
    assert await count_rows(Order, id=body["id"]) == 1


async def test_create_entrega_exige_endereco_e_cobra_taxa(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client, delivery_fee="7.50")
    product = await create_product(client, restaurant_id, base_price="30.00")
    await add_item(client, customer_id, product["id"], 1)

    sem_endereco = await client.post(
        f"/customers/{customer_id}/checkout",
        json={"delivery_type": "entrega", "confirmed": True},
    )
    assert sem_endereco.status_code == 400
    assert "endereço" in sem_endereco.json()["detail"].lower()

    body = await checkout(
        client, customer_id, delivery_type="entrega", address="Rua das Flores 123", payment_method="dinheiro"
    )
    assert body["delivery_fee"] == "7.50"
    assert body["total"] == "37.50"
    assert body["address"] == "Rua das Flores 123"
    assert body["payment_method"] == "dinheiro"


async def test_create_sem_confirmacao_falha(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id, base_price="10.00")
    await add_item(client, customer_id, product["id"], 1)

    response = await client.post(
        f"/customers/{customer_id}/checkout", json={"delivery_type": "retirada", "confirmed": False}
    )
    assert response.status_code == 400
    assert "Confirme" in response.json()["detail"]


async def test_create_carrinho_vazio_falha(client: AsyncClient) -> None:
    customer_id, _ = await setup(client)
    response = await client.post(f"/customers/{customer_id}/checkout", json={"delivery_type": "retirada"})
    assert response.status_code == 400
    assert "vazio" in response.json()["detail"]


async def test_create_produto_inativado_nao_vende(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id, base_price="10.00")
    await add_item(client, customer_id, product["id"], 1)
    await client.put(f"/products/{product['id']}", json={"status": "inactive"})

    response = await client.post(f"/customers/{customer_id}/checkout", json={"delivery_type": "retirada"})
    assert response.status_code == 409
    assert "indisponível" in response.json()["detail"]


async def test_create_snapshot_preco_nao_muda_com_promocao(client: AsyncClient) -> None:
    customer_id, restaurant_id = await setup(client)
    product = await create_product(client, restaurant_id, base_price="10.00")
    await add_item(client, customer_id, product["id"], 1)
    await client.put(f"/products/{product['id']}", json={"base_price": "99.90"})

    body = await checkout(client, customer_id)
    assert body["items"][0]["unit_price"] == "10.00"
    assert body["subtotal"] == "10.00"