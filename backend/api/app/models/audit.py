# app/models/audit.py
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import text
from app.db.base_class import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id        = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id   = Column(UUID(as_uuid=True), index=True, nullable=True)  # actor
    accion    = Column(String, nullable=False)
    payload   = Column(JSONB, nullable=True)
    ip        = Column(String, nullable=True)
    ua        = Column(Text, nullable=True)
    # En tu BD hoy aparece NULLABLE. Dejamos default now() aquí para nuevas filas.
    creado_en = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=True)
