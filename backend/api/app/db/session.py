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

# Configuración para Supabase (detecta si es pooler o directa)
is_pooler = "pooler" in db_url.lower() or ":6543" in db_url

if is_pooler:
    # Usar NullPool para conexión con pooler (PgBouncer)
    from sqlalchemy.pool import NullPool
    
    engine = create_engine(
        db_url,
        poolclass=NullPool,
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 10,
        },
        echo=False,
    )
    print("[DB] Using NullPool (Pooler/PgBouncer mode)")
else:
    # Usar pool normal para conexión directa
    engine = create_engine(
        db_url,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=300,
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",
        },
        echo=False,
    )
    print("[DB] Using standard pool (Direct connection)")

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