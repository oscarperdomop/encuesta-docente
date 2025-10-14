# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import re

def _mask(u: str) -> str:
    """Enmascara la contraseña en la URL para logs seguros"""
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", u)

# Log de la URL enmascarada para debugging
db_url = settings.db_url
print(f"[DB] Using: {_mask(db_url)}")
print(f"[DB] Connection type: {'POOLER' if 'pooler' in db_url.lower() else 'DIRECT'}")

# Configuración optimizada para CONEXIÓN DIRECTA a Supabase
# Si usas pooler, el config.py lo convierte automáticamente a directa
engine = create_engine(
    db_url,
    # Pool settings (para conexión directa)
    pool_size=settings.DB_POOL_SIZE,              # 5 conexiones base
    max_overflow=settings.DB_MAX_OVERFLOW,        # 10 conexiones extra en picos
    pool_timeout=settings.DB_POOL_TIMEOUT,        # 30s timeout
    pool_recycle=settings.DB_POOL_RECYCLE,        # Recicla cada 5 min
    pool_pre_ping=settings.DB_POOL_PRE_PING,      # Verifica conexión antes de usar
    
    # Connect args (ya incluye sslmode y timeouts desde config.py)
    connect_args=settings.db_connect_args,
    
    # Echo SQL queries (útil para debugging, cambiar a False en producción)
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


# Función opcional para verificar la conexión al inicio
def check_db_connection():
    """Verifica que la conexión a la base de datos funcione"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("[DB] ✓ Connection successful")
            return True
    except Exception as e:
        print(f"[DB] ✗ Connection failed: {e}")
        return False