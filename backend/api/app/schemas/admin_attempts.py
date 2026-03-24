from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class GrantExtraIn(BaseModel):
    survey_id: UUID
    user_id: UUID
    extra: int


class LimitsOut(BaseModel):
    survey_id: UUID
    user_id: UUID
    max_intentos: int
    extra_otorgados: int
    total_permitidos: int
