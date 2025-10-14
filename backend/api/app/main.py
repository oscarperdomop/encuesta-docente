from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    logger.info(f"[APP] CORS Origins: {settings.cors_list}")
    
    # Verificar conexión a la base de datos
    if check_db_connection():
        logger.info("[APP] ✓ Database connection established")
    else:
        logger.error("[APP] ✗ Database connection failed - App may not work properly")


@app.on_event("shutdown")
async def shutdown_event():
    """Ejecuta al cerrar la aplicación"""
    logger.info("[APP] Shutting down...")
    # Cerrar el engine de SQLAlchemy
    engine.dispose()
    logger.info("[APP] ✓ Database connections closed")


# ============================================
# MANEJADORES DE ERRORES GLOBALES
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Maneja excepciones no capturadas"""
    logger.error(f"[ERROR] Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.ENV == "dev" else "An error occurred"
        }
    )


# ============================================
# ROUTERS VERSIONADOS
# ============================================

app.include_router(health.router,   prefix=API_V1_PREFIX)
app.include_router(auth.router,     prefix=API_V1_PREFIX)
app.include_router(catalogs.router, prefix=API_V1_PREFIX)
app.include_router(attempts.router, prefix=API_V1_PREFIX)
app.include_router(queue_ep.router, prefix=API_V1_PREFIX)
app.include_router(sessions.router, prefix=API_V1_PREFIX)
app.include_router(admin_surveys.router, prefix=API_V1_PREFIX)

# Admin routes
app.include_router(admin_imports.router,  prefix=f"{API_V1_PREFIX}/admin")
app.include_router(admin_attempts.router, prefix=f"{API_V1_PREFIX}/admin")
app.include_router(admin_roles.router,    prefix=f"{API_V1_PREFIX}/admin")


# ============================================
# ENDPOINTS DE SALUD
# ============================================

@app.get("/")
def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Bienvenido a la API de Encuestas Docentes",
        "version": "1.0.0",
        "environment": settings.ENV,
        "docs": "/docs",
        "redoc": "/redoc",
        "api_v1": API_V1_PREFIX,
        "health_checks": {
            "basic": "/health",
            "database": "/api/v1/health/db"
        }
    }


@app.get("/health")
def health_root():
    """Health check básico sin dependencias"""
    return {
        "status": "ok",
        "message": "API funcionando correctamente",
        "environment": settings.ENV
    }


@app.get("/api/v1/health/db")
def health_db():
    """Health check de la base de datos"""
    try:
        with SessionLocal() as session:
            # Ejecutar query simple para verificar conexión
            result = session.execute(text("SELECT 1 as healthcheck"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                return {
                    "status": "ok",
                    "database": "connected",
                    "message": "Database connection successful"
                }
            else:
                raise Exception("Unexpected query result")
                
    except Exception as e:
        logger.error(f"[HEALTH] Database check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "database": "disconnected",
                "message": f"Database connection failed: {str(e)}"
            }
        )


# ============================================
# ENDPOINT DE INFO (útil para debugging)
# ============================================

@app.get("/api/v1/info")
def app_info():
    """Información de configuración (solo en desarrollo)"""
    if settings.ENV != "dev":
        raise HTTPException(status_code=404, detail="Not found")
    
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.ENV,
        "cors_origins": settings.cors_list,
        "jwt_algorithm": settings.JWT_ALGORITHM,
        "jwt_expire_minutes": settings.JWT_EXPIRE_MINUTES,
        "database": {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_recycle": settings.DB_POOL_RECYCLE,
        }
    }