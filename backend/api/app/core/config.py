from __future__ import annotations
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parents[2]  # .../api
ENV_FILE = API_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "Encuesta Docente API"
    ENV: str = "prod"

    # JWT
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: str = "https://encuesta-docente-f.vercel.app,https://encuesta-docente.onrender.com"

    # Database
    DATABASE_URL: str | None = None
    SQLALCHEMY_DATABASE_URI: str | None = None

    @property
    def cors_list(self) -> list[str]:
        """Lista de orígenes permitidos para CORS"""
        return [o.strip() for o in (self.CORS_ORIGINS or "").split(",") if o.strip()]

    @property
    def db_url(self) -> str:
        """URL de base de datos unificada"""
        url = (self.DATABASE_URL or self.SQLALCHEMY_DATABASE_URI or "").strip()
        
        if not url:
            raise ValueError("Falta DATABASE_URL")
        
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()