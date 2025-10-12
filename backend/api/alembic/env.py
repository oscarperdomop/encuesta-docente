# api/alembic/env.py
from __future__ import annotations

import os
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# --- Carga .env (api/.env) ---
try:
    from dotenv import load_dotenv  # requires python-dotenv
except Exception:
    load_dotenv = None

API_DIR = Path(__file__).resolve().parents[1]  # .../api
if load_dotenv:
    load_dotenv(API_DIR / ".env")

# --- Limpia variables de entorno de PG que estorban y asegura UTF-8 ---
for var in ("PGSERVICE", "PGSERVICEFILE", "PGSYSCONFDIR", "PGAPPNAME", "PGOPTIONS", "PGPASSFILE"):
    os.environ.pop(var, None)
os.environ.setdefault("PGCLIENTENCODING", "UTF8")

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# --- URL de conexión ---
# Preferimos SQLALCHEMY_DATABASE_URI de .env; fallback a sqlalchemy.url en alembic.ini
db_url = (
    os.getenv("SQLALCHEMY_DATABASE_URI")
    or os.getenv("DATABASE_URL")  # por si acaso
    or config.get_main_option("sqlalchemy.url")
)

if not db_url:
    raise RuntimeError(
        "No se encontró URL de BD. Define SQLALCHEMY_DATABASE_URI en api/.env "
        "o sqlalchemy.url en api/alembic.ini"
    )

# Fuerza sslmode=require cuando es Supabase y no está presente
if ("supabase.co" in db_url or "supabase.com" in db_url) and "sslmode=" not in db_url:
    sep = "&" if "?" in db_url else "?"
    db_url = f"{db_url}{sep}sslmode=require"

# Refleja la URL en la configuración de Alembic (para scripts/env internos)
context.config.set_main_option("sqlalchemy.url", db_url)

# --- Carga metadata de modelos para autogenerate ---
# Ajustado a tu estructura: api/app/models/{user,docente,encuesta}.py
try:
    # 1) Base centralizada (recomendado: api/app/db/base.py con Base = declarative_base() e import de modelos)
    from app.db.base import Base  # type: ignore
except Exception:
    # 2) Si no existe, intento directo: importar modelos para registrar mapeos
    Base = None
    try:
        from app.models import user, docente, encuesta  # noqa: F401
        # Si cada modelo define Base = declarative_base() por separado, crea inconsistencias.
        # Lo ideal es un único Base central (app/db/base.py). Si existe 'user.Base', úsalo:
        if hasattr(user, "Base"):
            Base = user.Base  # type: ignore
    except Exception:
        pass

target_metadata = Base.metadata if Base is not None else None

# --- Utilidad: redacción segura de URL para logs (sin password) ---
def _redact_url(url: str) -> str:
    # postgresql+psycopg2://USER:PASSWORD@host:port/db?...
    try:
        prefix, rest = url.split("://", 1)
        if "@" in rest and ":" in rest.split("@", 1)[0]:
            creds, tail = rest.split("@", 1)
            user, _pwd = creds.split(":", 1)
            return f"{prefix}://{user}:***@{tail}"
        return url
    except Exception:
        return url

print("DEBUG sqlalchemy.url =", _redact_url(db_url))

# --- Offline / Online runners ---
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Para Supabase, mantener NullPool es suficiente en migraciones
    connect_args = {}
    # Redundante pero útil si la URL no trae sslmode y es Supabase:
    if "supabase.co" in db_url or "supabase.com" in db_url:
        connect_args.setdefault("sslmode", "require")

    engine = create_engine(
        db_url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
