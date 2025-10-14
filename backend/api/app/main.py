from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import logging

from app.core.config import settings
from app.db.session import SessionLocal, engine, check_db_connection

from app.api.v1.endpoints import (
    health, auth, catalogs, attempts, sessions,
    admin_attempts, admin_surveys, admin_imports, admin_roles
)
from app.api.v1.endpoints import queue as queue_ep

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title=settings.APP_NAME,
    description="API para el sistema de encuestas docentes",
    version="1.0.0",
)

# CORS (orígenes explícitos en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# EVENTOS DE STARTUP Y SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup_event():
    """Ejecuta al iniciar la aplicación"""
    logger.info(f"[APP] Starting {settings.APP_NAME}")
    logger.info(f"[APP] Environment: {settings.ENV}")
    
    # Verificar conexión a la base de datos
    if check_db_connection():
        logger.info("[APP] ✓ Database connection established")
    else:
        logger.error("[APP] ✗ Database connection failed")


@app.on_event("shutdown")
async def shutdown_event():
    """Ejecuta al cerrar la aplicación"""
    logger.info("[APP] Shutting down...")
    engine.dispose()
    logger.info("[APP] ✓ Database connections closed")


# ============================================
# ROUTERS
# ============================================

app.include_router(health.router,   prefix=API_V1_PREFIX)
app.include_router(auth.router,     prefix=API_V1_PREFIX)
app.include_router(catalogs.router, prefix=API_V1_PREFIX)
app.include_router(attempts.router, prefix=API_V1_PREFIX)
app.include_router(queue_ep.router, prefix=API_V1_PREFIX)
app.include_router(sessions.router, prefix=API_V1_PREFIX)
app.include_router(admin_surveys.router, prefix=API_V1_PREFIX)

# Admin
app.include_router(admin_imports.router,  prefix=f"{API_V1_PREFIX}/admin")
app.include_router(admin_attempts.router, prefix=f"{API_V1_PREFIX}/admin")
app.include_router(admin_roles.router,    prefix=f"{API_V1_PREFIX}/admin")


# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
def root():
    """Endpoint raíz"""
    return {
        "message": "Bienvenido a la API de Encuestas Docentes",
        "version": "1.0.0",
        "docs": "/docs",
        "api_v1": API_V1_PREFIX,
    }


@app.get("/health")
def health_root():
    """Health check básico"""
    return {"status": "ok", "message": "API funcionando correctamente"}


@app.get("/api/v1/health/db")
def health_db():
    """Health check de base de datos"""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"[HEALTH] Database check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "message": str(e)}
        )