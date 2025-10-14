from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal

from app.api.v1.endpoints import (
    health, auth, catalogs, attempts, sessions,
    admin_attempts, admin_surveys, admin_imports, admin_roles
)
from app.api.v1.endpoints import queue as queue_ep

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

# Routers versionados
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

# Health básicos
@app.get("/health")
def health_root():
    return {"status": "ok", "message": "API funcionando correctamente"}

@app.get("/api/v1/health/db")
def health_db():
    with SessionLocal() as s:
        s.execute(text("SELECT 1"))
    return {"db": "ok"}

@app.get("/")
def root():
    return {
        "message": "Bienvenido a la API de Encuestas Docentes",
        "version": "1.0.0",
        "docs": "/docs",
        "api_v1": API_V1_PREFIX,
    }
