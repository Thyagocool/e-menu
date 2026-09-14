from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.whatsapp.models import Conversation, Customer, Message


class CustomerRepository:
    async def get_by_phone(self, session: AsyncSession, restaurant_id: int, phone: str) -> Customer | None:
        return await session.scalar(
            select(Customer).where(Customer.restaurant_id == restaurant_id, Customer.phone == phone)
        )

    async def create(
        self, session: AsyncSession, restaurant_id: int, phone: str, name: str | None
    ) -> Customer:
        customer = Customer(restaurant_id=restaurant_id, phone=phone, name=name)
        session.add(customer)
        return customer


class ConversationRepository:
    async def get_by_customer(
        self, session: AsyncSession, restaurant_id: int, customer_id: int
    ) -> Conversation | None:
        return await session.scalar(
            select(Conversation).where(
                Conversation.restaurant_id == restaurant_id, Conversation.customer_id == customer_id
            )
        )

    async def create(
        self, session: AsyncSession, restaurant_id: int, customer_id: int
    ) -> Conversation:
        conversation = Conversation(restaurant_id=restaurant_id, customer_id=customer_id)
        session.add(conversation)
        return conversation


class MessageRepository:
    async def get_by_external_id(
        self, session: AsyncSession, external_message_id: str
    ) -> Message | None:
        return await session.scalar(
            select(Message).where(Message.external_message_id == external_message_id)
        )

    async def create(
        self,
        session: AsyncSession,
        conversation_id: int,
        external_message_id: str,
        content: str,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            direction="inbound",
            external_message_id=external_message_id,
            content=content,
        )
        session.add(message)
        return message