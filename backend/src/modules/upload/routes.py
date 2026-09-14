from fastapi import APIRouter, File, UploadFile

from src.infra.storage import save_image

router = APIRouter(tags=["upload"])


@router.post("/upload", status_code=201)
async def upload_image(file: UploadFile = File(...)) -> dict:
    content = await file.read()
    url = save_image(content, file.filename or "", file.content_type or "")
    return {"url": url}