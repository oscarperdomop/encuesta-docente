import uuid
from sqlalchemy import (
  Column, Integer, String, ForeignKey, DateTime, func, UniqueConstraint, SmallInteger, text
)

from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Attempt(Base):  
    __tablename__ = "attempts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id = Column(PGUUID(as_uuid=True), ForeignKey("surveys.id"), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    teacher_id = Column(PGUUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False, index=True)

    intento_nro = Column(SmallInteger, nullable=False)
    estado = Column(String, nullable=False, index=True)  # en_progreso|enviado|expirado|fallido
    progreso_json = Column(JSONB)

    # <-- estos dos campos faltaban en tu modelo
    
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    expires_at = Column(DateTime(timezone=True))

    # relaciones
    responses = relationship("Response", back_populates="attempt", cascade="all, delete-orphan")


class Response(Base):
    __tablename__ = "responses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(PGUUID(as_uuid=True), ForeignKey("attempts.id"), nullable=False, index=True)
    question_id = Column(PGUUID(as_uuid=True), ForeignKey("questions.id"), nullable=False, index=True)

    valor_likert = Column(Integer)  # NULL para Q16
    texto = Column(JSONB)           # NULL para likert

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    attempt = relationship("Attempt", back_populates="responses")