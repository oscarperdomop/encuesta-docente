from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.attempt import Attempt
from app.schemas.sessions import SessionCloseOut

router = APIRouter(tags=["sessions"])

def _expire_stale_attempts(db: Session, survey_id: UUID, user_id: UUID) -> int:
    now = datetime.now(timezone.utc)
    updated = (
        db.query(Attempt)
        .filter(
            Attempt.survey_id == survey_id,
            Attempt.user_id == user_id,
            Attempt.estado == "en_progreso",
            Attempt.expires_at.isnot(None),
            Attempt.expires_at <= now,
        )
        .update({Attempt.estado: "expirado"}, synchronize_session=False)
    )
    if updated:
        db.commit()
    return updated

@router.post("/sessions/close", response_model=SessionCloseOut)
def close_session(
    survey_id: UUID = Query(..., description="ID de la encuesta a cerrar"),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """
    Cierra el 'turno' del usuario para esa encuesta si NO hay attempts en_progreso.
    No obliga a evaluar TODOS los autorizados; solo valida que no quedaste con docentes a medias.
    """
    # user_id (soporta user model o dict del token)
    user_id = getattr(current, "id", None) or current.get("sub") or current.get("id")

    if not user_id:
        raise HTTPException(status_code=401, detail="No se pudo obtener el usuario del token")

    # 1) Expirar por tiempo
    _expire_stale_attempts(db, survey_id, user_id)

    # 2) Conteos por estado
    rows = (
        db.query(Attempt.estado, func.count(Attempt.id))
        .filter(Attempt.survey_id == survey_id, Attempt.user_id == user_id)
        .group_by(Attempt.estado)
        .all()
    )
    counts = {estado: int(n) for estado, n in rows}
    en_progreso = counts.get("en_progreso", 0)
    enviados = counts.get("enviado", 0)
    expirados = counts.get("expirado", 0)
    fallidos  = counts.get("fallido", 0)

    # 3) Bloquear si hay pendientes en progreso
    if en_progreso > 0:
        raise HTTPException(
            status_code=409,
            detail="Aún tienes docentes en progreso. Termina o deja expirar antes de cerrar el turno."
        )

    # (Opcional) puedes exigir al menos un 'enviado' en la sesión actual:
    # if enviados == 0:
    #     raise HTTPException(409, "No hay envíos. Nada que cerrar.")

    return SessionCloseOut(
        survey_id=survey_id,
        closed=True,
        enviados=enviados,
        en_progreso=en_progreso,
        expirados=expirados,
        fallidos=fallidos,
        closed_at=datetime.now(timezone.utc),
    )
