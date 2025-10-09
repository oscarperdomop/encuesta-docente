# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,  # lee DATABASE_URL
    pool_pre_ping=True,
    poolclass=NullPool,                # <- clave con PgBouncer (pooler)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # siempre cerrar
