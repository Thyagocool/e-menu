import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from src.config import get_settings
from src.infra.database import SessionLocal
from src.modules.whatsapp.models import Conversation, Customer, Message
from src.modules.whatsapp.provider import WhatsAppProvider
from tests.conftest import create_restaurant


def meta_payload(
    msg_id: str = "wamid-1",
    customer: str = "5511987654321",
    restaurant: str = "5511999991234",
    text: str = "Oi, quero uma pizza",
    name: str = "Maria",
) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"field": "messages", "value": {
            "messages": [{"from": customer, "id": msg_id, "timestamp": "1700000000", "text": {"body": text}}],
            "contacts": [{"wa_id": customer, "profile": {"name": name}}],
            "metadata": {"display_phone_number": restaurant, "phone_number_id": "123456"},
        }}]}]}


async def count_rows(model, **filters) -> int:
    async with SessionLocal() as session:
        query = select(func.count()).select_from(model)
        for field, value in filters.items():
            query = query.where(getattr(model, field) == value)
        return await session.scalar(query)


async def test_webhook_creates_customer_conversation_message(client: AsyncClient) -> None:
    await create_restaurant(client, name="Pizzaria Sol", slug="pizzaria-sol", whatsapp_phone="5511999991234")
    response = await client.post("/webhooks/whatsapp", json=meta_payload())
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "reply" in response.json()  # o garçom (IA) respondeu
    assert await count_rows(Customer) == 1
    assert await count_rows(Conversation) == 1
    assert await count_rows(Message) == 2  # inbound + resposta outbound


async def test_webhook_is_idempotent(client: AsyncClient) -> None:
    await create_restaurant(client, name="Pizzaria Sol", slug="pizzaria-sol", whatsapp_phone="5511999991234")
    first = (await client.post("/webhooks/whatsapp", json=meta_payload())).json()
    second = (await client.post("/webhooks/whatsapp", json=meta_payload())).json()
    assert first["message_id"] == second["message_id"]
    assert await count_rows(Message) == 2  # reenvio não duplica (inbound + outbound)
    assert await count_rows(Conversation) == 1


async def test_webhook_reuses_customer_and_conversation(client: AsyncClient) -> None:
    await create_restaurant(client, name="Pizzaria Sol", slug="pizzaria-sol", whatsapp_phone="5511999991234")
    await client.post("/webhooks/whatsapp", json=meta_payload(msg_id="wamid-1"))
    await client.post("/webhooks/whatsapp", json=meta_payload(msg_id="wamid-2", text="Quero borda"))
    assert await count_rows(Customer) == 1
    assert await count_rows(Conversation) == 1
    assert await count_rows(Message) == 4  # 2 inbound + 2 respostas


async def test_webhook_isolates_restaurants(client: AsyncClient) -> None:
    await create_restaurant(client, name="Pizzaria Sol", slug="pizzaria-sol", whatsapp_phone="5511999991234")
    await create_restaurant(client, name="Bar do Zé", slug="bar-do-ze", whatsapp_phone="5511888884321")
    await client.post("/webhooks/whatsapp", json=meta_payload())
    await client.post(
        "/webhooks/whatsapp",
        json=meta_payload(msg_id="wamid-2", restaurant="5511888884321", text="Uma cerveja"),
    )
    assert await count_rows(Customer) == 2
    assert await count_rows(Conversation) == 2


async def test_webhook_invalid_payload(client: AsyncClient) -> None:
    assert (await client.post("/webhooks/whatsapp", json={})).status_code == 400


async def test_webhook_malformed_body_is_400(client: AsyncClient) -> None:
    response = await client.post("/webhooks/whatsapp", content=b"{nao-json")
    assert response.status_code == 400


async def test_webhook_unknown_restaurant(client: AsyncClient) -> None:
    response = await client.post("/webhooks/whatsapp", json=meta_payload())
    assert response.status_code == 404


async def test_webhook_signature_rejected_when_secret_configured(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "whatsapp_app_secret", "segredo")
    response = await client.post("/webhooks/whatsapp", json=meta_payload())
    assert response.status_code == 401


async def test_webhook_signature_accepted_when_valid(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await create_restaurant(
        client, name="Pizzaria Sol", slug="pizzaria-sol", whatsapp_phone="5511999991234"
    )
    monkeypatch.setattr(get_settings(), "whatsapp_app_secret", "segredo")
    raw = json.dumps(meta_payload()).encode()
    expected = "sha256=" + hmac.new(b"segredo", raw, hashlib.sha256).hexdigest()
    response = await client.post(
        "/webhooks/whatsapp",
        content=raw,
        headers={"Content-Type": "application/json", "x-hub-signature-256": expected},
    )
    assert response.status_code == 200


async def test_webhook_verify_hub(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "whatsapp_verify_token", "meu-token")
    ok = await client.get(
        "/webhooks/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "meu-token", "hub.challenge": "987654"},
    )
    assert ok.status_code == 200
    assert ok.text == "987654"
    bad = await client.get(
        "/webhooks/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "errado", "hub.challenge": "1"},
    )
    assert bad.status_code == 403


async def test_provider_send_stub_without_credentials() -> None:
    provider = WhatsAppProvider()
    assert provider.send("5511987654321", "Oi").__await__ is not None
    message_id = await provider.send("5511987654321", "Oi")
    assert message_id.startswith("stub-")