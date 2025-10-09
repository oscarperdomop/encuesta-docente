from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class SessionCloseOut(BaseModel):
    survey_id: UUID
    closed: bool
    enviados: int
    en_progreso: int
    expirados: int
    fallidos: int
    closed_at: Optional[datetime] = None
