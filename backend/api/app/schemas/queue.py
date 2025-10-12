from __future__ import annotations
from typing import Literal, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

QueueState = Literal["pendiente", "en_progreso", "enviado"]

class QueueItemOut(BaseModel):
    teacher_id: UUID
    teacher_nombre: str
    estado: QueueState
    attempt_id: Optional[UUID] = None
    intento_nro: Optional[int] = None
    expires_at: Optional[datetime] = None

class QueueOut(BaseModel):
    survey_id: UUID
    summary: dict = Field(
        default_factory=lambda: {"pendiente": 0, "en_progreso": 0, "enviado": 0}
    )
    items: list[QueueItemOut]
