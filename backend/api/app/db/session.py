from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
import re

def _mask(u: str) -> str:
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", u)

print("[DB] Using:", _mask(settings.db_url))

engine = create_engine(
    settings.db_url,
    pool_pre_ping=True,
    poolclass=NullPool,             # obligatorio con PgBouncer (pooler)
    connect_args={"sslmode": "require"},  # redundante si ya va en la URL, pero seguro
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
