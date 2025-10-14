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

    # CORS (coma-separado)
    CORS_ORIGINS: str = "https://encuesta-docente-f.vercel.app,https://encuesta-docente.onrender.com"

    # DB (usa SOLO una; en Render usa DATABASE_URL)
    DATABASE_URL: str | None = None
    SQLALCHEMY_DATABASE_URI: str | None = None

    # Database Pool Settings (optimizados para Render + Supabase)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 300  # 5 minutos
    DB_POOL_PRE_PING: bool = True
    DB_CONNECT_TIMEOUT: int = 10
    DB_STATEMENT_TIMEOUT: int = 30000  # 30 segundos en milisegundos

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in (self.CORS_ORIGINS or "").split(",") if o.strip()]

    @property
    def db_url(self) -> str:
        """
        URL unificada para SQLAlchemy.
        - MANTIENE pooler para evitar problemas de IPv6 en Render
        - Fuerza sslmode=require para Supabase
        - Agrega connect_timeout
        """
        url = (self.DATABASE_URL or self.SQLALCHEMY_DATABASE_URI or "").strip()
        
        if not url:
            raise ValueError("Falta DATABASE_URL (o SQLALCHEMY_DATABASE_URI).")
        
        # NO convertir pooler - es necesario para IPv4 en Render
        # El pooler usa IPv4 mientras que la conexión directa intenta IPv6
        
        # Asegurar SSL para Supabase
        if ("supabase.co" in url or "supabase.com" in url or "pooler.supabase.com" in url) and "sslmode=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"
        
        # Agregar connect_timeout si no existe
        if "connect_timeout=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}connect_timeout={self.DB_CONNECT_TIMEOUT}"
        
        return url
    
    @property
    def db_connect_args(self) -> dict:
        """Argumentos de conexión optimizados para Supabase"""
        args = {
            "connect_timeout": self.DB_CONNECT_TIMEOUT,
        }
        
        # Agregar statement_timeout solo si usamos conexión directa
        if "pooler" not in self.db_url:
            args["options"] = f"-c statement_timeout={self.DB_STATEMENT_TIMEOUT}"
        
        return args


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()