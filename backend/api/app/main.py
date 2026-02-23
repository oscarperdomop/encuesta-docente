from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import logging

from app.core.config import settings
from app.api.v1.endpoints import health, auth, catalogs, attempts, sessions, admin_attempts, admin_surveys, admin_imports, admin_roles, admin_reports
from app.api.v1.endpoints import queue as queue_ep

from app.db.session import check_db_connection, SessionLocal  # <- FIX

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title=settings.APP_NAME,
    description="API para el sistema de encuestas docentes",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info(f"[APP] Starting {settings.APP_NAME}")
    logger.info(f"[APP] Environment: {settings.ENV}")

    if check_db_connection():
        logger.info("[APP] ✓ Database connection established")
    else:
        logger.error("[APP] ✗ Database connection failed")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("[APP] Shutting down...")
    # No llames engine.dispose() si no importas engine
    logger.info("[APP] ✓ Shutdown complete")

# Routers
app.include_router(health.router,   prefix=API_V1_PREFIX)
app.include_router(auth.router,     prefix=API_V1_PREFIX)
app.include_router(catalogs.router, prefix=API_V1_PREFIX)
app.include_router(attempts.router, prefix=API_V1_PREFIX)
app.include_router(queue_ep.router, prefix=API_V1_PREFIX)
app.include_router(sessions.router, prefix=API_V1_PREFIX)
app.include_router(admin_surveys.router, prefix=API_V1_PREFIX)

app.include_router(admin_imports.router,  prefix=f"{API_V1_PREFIX}/admin")
app.include_router(admin_attempts.router, prefix=f"{API_V1_PREFIX}/admin")
app.include_router(admin_roles.router,    prefix=f"{API_V1_PREFIX}/admin")
app.include_router(admin_reports.router,  prefix=f"{API_V1_PREFIX}/admin")

@app.get("/")
def root():
    return {
        "message": "Bienvenido a la API de Encuestas Docentes",
        "version": "1.0.0",
        "docs": "/docs",
        "api_v1": API_V1_PREFIX,
    }

@app.get("/health")
def health_root():
    return {"status": "ok", "message": "API funcionando correctamente"}

@app.get("/api/v1/health/db")
def health_db():
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"[HEALTH] Database check failed: {e}")
        raise HTTPException(status_code=503, detail={"status": "error", "message": str(e)})