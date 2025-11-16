from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, conint, field_validator, model_validator


# ---------- Entradas ----------

class AttemptsCreateIn(BaseModel):
    survey_id: UUID
    teacher_ids: List[UUID] = Field(min_items=1)


class SubmitAnswerIn(BaseModel):
    question_id: UUID
    value: conint(ge=1, le=5)  # 1..5


class Q16In(BaseModel):
    positivos: Optional[str] = None
    mejorar: Optional[str] = None
    comentarios: Optional[str] = None


class SubmitIn(BaseModel):
    answers: List[SubmitAnswerIn] = Field(min_items=15)
    q16: Optional[Q16In] = None
    textos: Optional[Q16In] = None
    
    @model_validator(mode='after')
    def normalize_q16_fields(self):
        """Normaliza textos a q16 si q16 no está presente"""
        if not self.q16 and self.textos:
            self.q16 = self.textos
        return self
    
    class Config:
        # Permitir campos extra para compatibilidad
        extra = 'allow'


class AttemptPatchIn(BaseModel):
    # Progreso parcial (por ejemplo, valores marcados en la UI)
    progreso: Optional[dict[str, Any]] = None
    # Si True (por defecto), renueva la ventana de 30 min del intento
    renew: Optional[bool] = True


# ---------- Salidas ----------

class AttemptOut(BaseModel):
    id: UUID
    survey_id: UUID
    teacher_id: UUID
    estado: str
    intento_nro: int
    expires_at: Optional[datetime] = None


class ScoreSectionOut(BaseModel):
    section_id: UUID
    titulo: str
    score: float


class ScoreBundleOut(BaseModel):
    total: Optional[float] = None
    secciones: List[ScoreSectionOut] = Field(default_factory=list)


class SubmitOut(BaseModel):
    estado: str  # "enviado"
    scores: ScoreBundleOut

# sumar intentos
class AttemptsSummaryOut(BaseModel):
    survey_id: UUID
    used_sessions: int
    max_sessions: int
    remaining_sessions: int
    has_open_session: bool
    open_session_intento_nro: Optional[int] = None
    open_session_expires_at: Optional[datetime] = None
    blocked: bool

class NextItemOut(BaseModel):
    survey_id: UUID
    teacher_id: UUID
    teacher_nombre: Optional[str] = None
    attempt_id: UUID
    expires_at: Optional[datetime] = None
    intento_nro: int