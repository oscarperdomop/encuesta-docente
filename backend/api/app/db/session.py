# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
import re

DB_URI = settings.db_url  # <- usa SIEMPRE la propiedad unificada

# Log sanitizado (sin exponer la contraseña)
def _mask(u: str) -> str:
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", u)

print("[DB] Using:", _mask(DB_URI))

engine = create_engine(
    DB_URI,
    pool_pre_ping=True,
    poolclass=NullPool,                 # obligatorio con PgBouncer (pooler de Supabase)
    connect_args={"sslmode": "require"},  # redundante si ya va en la URL, pero seguro
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
