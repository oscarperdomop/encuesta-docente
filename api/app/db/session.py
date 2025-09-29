# api/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Usa la propiedad unificada (ya asegura sslmode=require si hace falta)
engine = create_engine(settings.db_url, pool_pre_ping =True, future=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
