import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.errors import DomainError
from src.modules.ai.usecases import AIService
from src.modules.restaurant.models import Restaurant
from src.modules.whatsapp.models import Message
from src.modules.whatsapp.provider import WhatsAppEvent, WhatsAppProvider
from src.modules.whatsapp.repository import (
    ConversationRepository,
    CustomerRepository,
    MessageRepository,
)
from src.modules.whatsapp.utils import normalize_phone

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(
        self,
        provider: WhatsAppProvider | None = None,
        customers: CustomerRepository | None = None,
        conversations: ConversationRepository | None = None,
        messages: MessageRepository | None = None,
        ai: AIService | None = None,
    ):
        self.provider = provider or WhatsAppProvider()
        self.customers = customers or CustomerRepository()
        self.conversations = conversations or ConversationRepository()
        self.messages = messages or MessageRepository()
        self.ai = ai or AIService()

    async def _find_restaurant(
        self, session: AsyncSession, restaurant_number: str | None
    ) -> Restaurant | None:
        if not restaurant_number:
            return None
        target = normalize_phone(restaurant_number)
        # ponytail: scan em memória, ok para dezenas de restaurantes no MVP;
        # migrar para coluna normalizada quando houver muitos
        result = await session.scalars(
            select(Restaurant).where(Restaurant.status == "active", Restaurant.whatsapp_phone.is_not(None))
        )
        for restaurant in result:
            if normalize_phone(restaurant.whatsapp_phone) == target:
                return restaurant
        return None

    async def handle_webhook(
        self, session: AsyncSession, payload: dict, raw_body: bytes, signature: str | None
    ) -> dict:
        if not self.provider.validate_signature(raw_body, signature):
            raise DomainError(401, "Assinatura do webhook inválida")
        event = self.provider.parse_event(payload)
        message, customer_id, duplicate, conversation_id = await self._process_inbound(session, event)
        message_id = message.id  # tools expiram a sessão; capturar antes
        if duplicate:
            return {"status": "ok", "message_id": message_id, "customer_id": customer_id}

        reply = await self.ai.handle_message(session, conversation_id, event.text)
        sent_id = await self.provider.send(event.customer_phone, reply)
        await self.messages.create(
            session, conversation_id, sent_id, reply, direction="outbound"
        )
        await session.commit()
        return {"status": "ok", "message_id": message_id, "customer_id": customer_id, "reply": reply}

    async def _process_inbound(
        self, session: AsyncSession, event: WhatsAppEvent
    ) -> tuple[Message, int, bool, int]:
        restaurant = await self._find_restaurant(session, event.restaurant_number)
        if restaurant is None:
            raise DomainError(404, "Nenhum restaurante ativo corresponde a este número de WhatsApp")

        customer = await self.customers.get_by_phone(
            session, restaurant.id, normalize_phone(event.customer_phone)
        )
        if customer is None:
            customer = await self.customers.create(
                session, restaurant.id, normalize_phone(event.customer_phone), event.customer_name
            )

        conversation = await self.conversations.get_by_customer(session, restaurant.id, customer.id)
        if conversation is None:
            conversation = await self.conversations.create(session, restaurant.id, customer.id)

        existing = await self.messages.get_by_external_id(session, event.external_message_id)
        if existing:
            return existing, customer.id, True, conversation.id  # idempotência: reenvio não duplica

        message = await self.messages.create(
            session, conversation.id, event.external_message_id, event.text
        )
        try:
            await session.commit()
        except IntegrityError:
            # ponytail: corrida rara entre duas entregas do mesmo webhook;
            # o unique de external_message_id garante a idempotência no banco
            await session.rollback()
            existing = await self.messages.get_by_external_id(session, event.external_message_id)
            if existing is None:
                raise
            return existing, customer.id, True, conversation.id
        await session.refresh(message)
        return message, customer.id, False, conversation.id