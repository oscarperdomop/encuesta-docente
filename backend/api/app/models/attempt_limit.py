# app/models/attempt_limit.py
from sqlalchemy import Column, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from app.db.base_class import Base  # mismo Base que usas en otros modelos

class AttemptLimit(Base):
    __tablename__ = "attempt_limits"

    survey_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    user_id   = Column(UUID(as_uuid=True), primary_key=True, index=True)

    # valores por defecto coherentes con tu lógica
    max_intentos    = Column(Integer, nullable=False, server_default=text("2"))
    extra_otorgados = Column(Integer, nullable=False, server_default=text("0"))
