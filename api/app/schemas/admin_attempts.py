# app/api/v1/endpoints/admin_attempts.py
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, conint
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_admin_user
from app.models.attempt_limit import AttemptLimit

router = APIRouter(tags=["admin:attempts"])

# Mantén este valor alineado con BASE_MAX_SESSIONS de attempts.py
BASE_MAX_SESSIONS = 2


class GrantExtraIn(BaseModel):
    survey_id: UUID
    user_id: UUID
    # permite sumar o restar extras (ej: 1, 2, -1, ...)
    extra: conint(ge=-100, le=100) = 1


class LimitsOut(BaseModel):
    survey_id: UUID
    user_id: UUID
    base: int
    extra_otorgados: int
    max_total: int


@router.post("/attempts/extra", response_model=LimitsOut, status_code=status.HTTP_200_OK)
def grant_attempt_extra(
    payload: GrantExtraIn,
    db: Session = Depends(get_db),
    current=Depends(get_admin_user),
):
    row = (
        db.query(AttemptLimit)
        .filter(
            AttemptLimit.survey_id == payload.survey_id,
            AttemptLimit.user_id == payload.user_id,
        )
        .first()
    )
    if not row:
        row = AttemptLimit(survey_id=payload.survey_id, user_id=payload.user_id, extra_otorgados=0)
        db.add(row)

    row.extra_otorgados = int(row.extra_otorgados or 0) + int(payload.extra)
    if row.extra_otorgados < 0:
        row.extra_otorgados = 0  # nunca negativo

    db.commit()
    db.refresh(row)

    base = BASE_MAX_SESSIONS
    return LimitsOut(
        survey_id=payload.survey_id,
        user_id=payload.user_id,
        base=base,
        extra_otorgados=int(row.extra_otorgados or 0),
        max_total=base + int(row.extra_otorgados or 0),
    )
