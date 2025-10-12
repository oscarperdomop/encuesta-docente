# app/api/v1/endpoints/admin_attempts.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_admin_user
from app.db.session import get_db
from app.models.attempt_limit import AttemptLimit
from app.services.audit import audit_log

router = APIRouter(tags=["admin:attempts"])

class GrantExtraIn(BaseModel):
    survey_id: str
    user_id: str
    extra: int

class LimitsOut(BaseModel):
    survey_id: str
    user_id: str
    max_intentos: int
    extra_otorgados: int
    total_permitidos: int

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
        row = AttemptLimit(
            survey_id=payload.survey_id,
            user_id=payload.user_id,
            # si no hay fila, usa defaults de la tabla/modelo
        )
        db.add(row)
        db.flush()

    # Ajustar extra
    row.extra_otorgados = (row.extra_otorgados or 0) + int(payload.extra)
    # Nunca negativo:
    if row.extra_otorgados < 0:
        row.extra_otorgados = 0

    db.commit()
    db.refresh(row)

    total = (row.max_intentos or 2) + (row.extra_otorgados or 0)
    return LimitsOut(
        survey_id=str(row.survey_id),
        user_id=str(row.user_id),
        max_intentos=row.max_intentos or 2,
        extra_otorgados=row.extra_otorgados or 0,
        total_permitidos=total,
    )
