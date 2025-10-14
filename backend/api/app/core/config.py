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
    JWT_SECRET: str = "change-me"     # => sobrescribe en Render
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # CORS (coma-separado). Ej:
    # "https://encuesta-docente-f.vercel.app,https://encuesta-docente.onrender.com"
    CORS_ORIGINS: str = "https://encuesta-docente-f.vercel.app,https://encuesta-docente.onrender.com"

    # DB (usa SOLO una; en Render usa DATABASE_URL)
    DATABASE_URL: str | None = None
    SQLALCHEMY_DATABASE_URI: str | None = None

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in (self.CORS_ORIGINS or "").split(",") if o.strip()]

    @property
    def db_url(self) -> str:
        """URL unificada para SQLAlchemy. Fuerza sslmode=require si falta."""
        url = (self.DATABASE_URL or self.SQLALCHEMY_DATABASE_URI or "").strip()
        if not url:
            raise ValueError("Falta DATABASE_URL (o SQLALCHEMY_DATABASE_URI).")
        if ("supabase.co" in url or "supabase.com" in url) and "sslmode=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"
        return url

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
