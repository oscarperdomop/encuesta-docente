# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import re

def _mask(u: str) -> str:
    """Enmascara la contraseña en la URL para logs seguros"""
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", u)

# Obtener URL y hacer logging
db_url = settings.db_url
print(f"[DB] Using: {_mask(db_url)}")
print(f"[DB] Connection type: {'POOLER' if 'pooler' in db_url.lower() else 'DIRECT'}")

# Configuración para CONEXIÓN DIRECTA a Supabase
engine = create_engine(
    db_url,
    # Pool settings optimizados para Render + Supabase
    pool_size=5,              # 5 conexiones base
    max_overflow=10,          # 10 conexiones extra en picos
    pool_timeout=30,          # 30s timeout para obtener conexión
    pool_recycle=300,         # Recicla conexiones cada 5 min
    pool_pre_ping=True,       # Verifica conexión antes de usar
    
    # Connect args con timeouts
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"  # 30 segundos
    },
    
    # Sin echo en producción
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection():
    """Verifica que la conexión a la base de datos funcione"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("[DB] ✓ Connection successful")
            return True
    except Exception as e:
        print(f"[DB] ✗ Connection failed: {e}")
        return False