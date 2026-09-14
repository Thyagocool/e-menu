import uuid
from pathlib import Path

from src.infra.errors import DomainError

MEDIA_DIR = Path("media")
ALLOWED_EXTENSIONS = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB


def save_image(content: bytes, filename: str, content_type: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS or ALLOWED_EXTENSIONS[ext] != content_type:
        raise DomainError(400, "Formato inválido. Use JPG, PNG ou WEBP.")
    if len(content) > MAX_SIZE:
        raise DomainError(400, "Imagem maior que 5MB.")
    MEDIA_DIR.mkdir(exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    (MEDIA_DIR / stored_name).write_bytes(content)
    return f"/media/{stored_name}"