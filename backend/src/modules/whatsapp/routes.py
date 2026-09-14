import json

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_session
from src.infra.errors import DomainError
from src.modules.whatsapp.usecases import WhatsAppService

router = APIRouter(prefix="/webhooks", tags=["whatsapp"])
service = WhatsAppService()


@router.get("/whatsapp", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    return service.provider.verify_hub(hub_mode, hub_verify_token, hub_challenge)


@router.post("/whatsapp")
async def receive_webhook(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise DomainError(400, "Body JSON inválido") from None
    signature = request.headers.get("x-hub-signature-256")
    return await service.handle_webhook(session, payload, raw_body, signature)