from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "e-menu"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://e_menu:e_menu@localhost:5433/e_menu"
    redis_url: str = "redis://localhost:6379/0"

    # WhatsApp Cloud API (vazios = modo dev: webhook sem validação, envio via stub)
    whatsapp_verify_token: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()