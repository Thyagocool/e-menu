import hashlib
import hmac
import logging
from dataclasses import dataclass

import httpx

from src.config import get_settings
from src.infra.errors import DomainError

logger = logging.getLogger(__name__)


@dataclass
class WhatsAppEvent:
    external_message_id: str
    customer_phone: str
    customer_name: str | None
    restaurant_number: str | None
    text: str


class WhatsAppProvider:
    """Fronteira com a WhatsApp Cloud API (Meta).

    Sem credenciais configuradas (MVP/dev): validação e envio viram no-op
    com log, permitindo rodar o fluxo localmente.
    """

    API_URL = "https://graph.facebook.com/v20.0"

    def __init__(self) -> None:
        self.settings = get_settings()

    def verify_hub(
        self, hub_mode: str | None, hub_verify_token: str | None, hub_challenge: str | None
    ) -> str:
        if (
            hub_mode == "subscribe"
            and hub_verify_token
            and self.settings.whatsapp_verify_token
            and hub_verify_token == self.settings.whatsapp_verify_token
            and hub_challenge
        ):
            return hub_challenge
        raise DomainError(403, "Falha na verificação do webhook")

    def validate_signature(self, raw_body: bytes, signature: str | None) -> bool:
        secret = self.settings.whatsapp_app_secret
        if not secret:
            return True  # dev: sem segredo configurado, aceita
        if not signature:
            return False
        expected = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def parse_event(self, payload: dict) -> WhatsAppEvent:
        try:
            value = payload["entry"][0]["changes"][0]["value"]
            message = value["messages"][0]
            contact = (value.get("contacts") or [{}])[0]
        except (KeyError, IndexError, TypeError):
            raise DomainError(400, "Payload do webhook inválido") from None
        external_message_id = message.get("id")
        text = (message.get("text") or {}).get("body")
        if not external_message_id or text is None or message.get("type") not in (None, "text"):
            # ponytail: tipo não-texto (imagem/áudio) fora do escopo do MVP
            raise DomainError(400, "Mensagem sem texto suportado")
        return WhatsAppEvent(
            external_message_id=external_message_id,
            customer_phone=message.get("from", ""),
            customer_name=(contact.get("profile") or {}).get("name"),
            restaurant_number=(value.get("metadata") or {}).get("display_phone_number"),
            text=text,
        )

    async def send(self, to: str, text: str) -> str:
        phone_number_id = self.settings.whatsapp_phone_number_id
        token = self.settings.whatsapp_token
        if not phone_number_id or not token:
            logger.info("send (dev stub, sem credenciais): to=%s text=%r", to, text)
            return f"stub-{len(text)}"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.API_URL}/{phone_number_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}},
            )
            response.raise_for_status()
            return response.json()["messages"][0]["id"]