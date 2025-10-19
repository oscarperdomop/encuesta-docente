# app/core/config.py
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
    ENV: str = "dev"

    # JWT
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    MAX_TURNOS: int = 2

    # CORS (puedes definir en Render: CORS_ORIGINS=https://encuesta-docente-f.vercel.app)
    CORS_ORIGINS: str = ""

    # DB URLs (acepta cualquiera de las dos)
    DATABASE_URL: str | None = None
    SQLALCHEMY_DATABASE_URI: str | None = None

    @property
    def cors_list(self) -> list[str]:
        if not self.CORS_ORIGINS:
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def db_url(self) -> str:
        """
        URL unificada para SQLAlchemy. Acepta DATABASE_URL o SQLALCHEMY_DATABASE_URI.
        Fuerza sslmode=require para Supabase si faltara.
        """
        url = (self.DATABASE_URL or self.SQLALCHEMY_DATABASE_URI or "").strip()
        if not url:
            raise ValueError("Define DATABASE_URL o SQLALCHEMY_DATABASE_URI en variables de entorno.")
        if ("supabase.co" in url or "supabase.com" in url) and "sslmode=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"
        return url

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
