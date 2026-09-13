import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(tags=["upload"])

MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(exist_ok=True)

ALLOWED = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/upload", status_code=201)
async def upload_image(file: UploadFile = File(...)) -> dict:
    ext = Path(file.filename or "").suffix.lower()
    content_type = file.content_type or ""
    if ext not in ALLOWED or ALLOWED[ext] != content_type:
        raise HTTPException(status_code=400, detail="Formato inválido. Use JPG, PNG ou WEBP.")
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Imagem maior que 5MB.")
    filename = f"{uuid.uuid4().hex}{ext}"
    (MEDIA_DIR / filename).write_bytes(content)
    return {"url": f"/media/{filename}"}