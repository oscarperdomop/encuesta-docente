# api/app/core/config.py
from __future__ import annotations

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


API_DIR = Path(__file__).resolve().parents[2]  # .../api
ENV_FILE = API_DIR / ".env"


class Settings(BaseSettings):
    # Pydantic v2: usa model_config (NO mezclar con class Config)
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "Encuesta Docente API"
    ENV: str = "dev"

    # JWT
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # DB URLs (acepta cualquiera de las dos)
    DATABASE_URL: str | None = None
    SQLALCHEMY_DATABASE_URI: str | None = None
    

    @property
    def db_url(self) -> str:
        """URL unificada para SQLAlchemy."""
        url = self.DATABASE_URL or self.SQLALCHEMY_DATABASE_URI
        if not url:
            raise ValueError("Define DATABASE_URL o SQLALCHEMY_DATABASE_URI en api/.env")
        # Forzar SSL en Supabase si falta
        if ("supabase.co" in url or "supabase.com" in url) and "sslmode=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Objeto listo para importar: from app.core.config import settings
settings = get_settings()
