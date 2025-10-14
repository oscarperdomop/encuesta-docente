# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings
import re

def _mask(u: str) -> str:
    """Enmascara la contraseña en la URL para logs seguros"""
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", u)

# Obtener URL
db_url = settings.db_url
print(f"[DB] Using: {_mask(db_url)}")

# Configuración simple para Render PostgreSQL
engine = create_engine(
    db_url,
    pool_size=5,              # 5 conexiones concurrentes
    max_overflow=10,          # Hasta 15 total en picos
    pool_timeout=30,          # 30s para obtener conexión
    pool_recycle=1800,        # Recicla cada 30 min
    pool_pre_ping=True,       # Verifica que la conexión esté viva
    echo=False,               # True para debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency para FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection():
    """Verifica que la conexión funcione"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("[DB] ✓ Connection successful")
                return True
            return False
    except Exception as e:
        print(f"[DB] ✗ Connection failed: {e}")
        return False