from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Tuple, Optional, Literal  # <-- agrega Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.docente import Teacher, SurveyTeacherAssignment
from app.models.attempt import Attempt
from app.models.encuesta import Survey
from app.schemas.queue import QueueOut, QueueItemOut

router = APIRouter(tags=["queue"])


# -------- helpers locales -------- #

def _extract_user_id(current) -> UUID:
    val = None
    if hasattr(current, "id"):
        val = getattr(current, "id", None)
    if val is None and isinstance(current, dict):
        val = current.get("sub") or current.get("id")
    if not val:
        raise HTTPException(status_code=401, detail="No se pudo obtener el usuario del token")
    return UUID(str(val))


def _expire_stale_attempts(db: Session, survey_id: UUID, user_id: UUID) -> int:
    """Pasa a 'expirado' los attempts en_progreso vencidos."""
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


# ----------------------------- endpoint público ----------------------------- #

@router.get("/queue", response_model=QueueOut)
def get_queue(
    survey_id: UUID = Query(..., description="ID de la encuesta"),
    scope: Literal["all", "selected"] = Query("all", description="Filtrado: all | selected"),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """
    Cola de docentes para el usuario en una encuesta:
    - scope=all      : docentes autorizados (pendiente / en_progreso / enviado)
    - scope=selected : solo docentes que YA tienen attempt (oculta 'pendiente')
    Nota: 'expirado' o 'fallido' se consideran 'pendiente' para el flujo UI.
    """
    user_id = _extract_user_id(current)

    # Verifica encuesta
    survey_exists = db.query(Survey.id).filter(Survey.id == survey_id).first()
    if not survey_exists:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")

    # Expira intentos vencidos antes de calcular estados
    _expire_stale_attempts(db, survey_id, user_id)

    # Catálogo de docentes elegibles para esta encuesta
    teachers = (
        db.query(Teacher.id, Teacher.nombre)
        .join(SurveyTeacherAssignment, SurveyTeacherAssignment.teacher_id == Teacher.id)
        .filter(
            SurveyTeacherAssignment.survey_id == survey_id,
            Teacher.estado == "activo",
        )
        .order_by(Teacher.nombre.asc())
        .all()
    )

    # Trae todos los attempts del usuario para esta encuesta
    now = datetime.now(timezone.utc)
    attempts = (
        db.query(Attempt)
        .filter(
            Attempt.survey_id == survey_id,
            Attempt.user_id == user_id,
        )
        .all()
    )

    # Para cada docente, determina el mejor estado visible (enviado > en_progreso > pendiente)
    state_by_teacher: Dict[UUID, Tuple[str, Optional[UUID], Optional[int], Optional[datetime]]] = {}

    for att in attempts:
        t_id = att.teacher_id
        prev = state_by_teacher.get(t_id, ("pendiente", None, None, None))
        prev_state = prev[0]

        is_active = att.estado == "en_progreso" and (att.expires_at is None or att.expires_at > now)

        if att.estado == "enviado":
            # Estado más fuerte; gana siempre
            state_by_teacher[t_id] = ("enviado", att.id, att.intento_nro, None)
        elif is_active:
            # Solo si no hay 'enviado' ya registrado
            if prev_state not in ("enviado", "en_progreso"):
                state_by_teacher[t_id] = ("en_progreso", att.id, att.intento_nro, att.expires_at)
        else:
            # expirado/fallido no cambian 'pendiente'
            if t_id not in state_by_teacher:
                state_by_teacher[t_id] = ("pendiente", None, None, None)

    # Construye items
    items: list[QueueItemOut] = []
    for tid, tname in teachers:
        estado, attempt_id, intento_nro, exp_at = state_by_teacher.get(
            tid, ("pendiente", None, None, None)
        )
        items.append(
            QueueItemOut(
                teacher_id=tid,
                teacher_nombre=tname,
                estado=estado,          # 'pendiente' | 'en_progreso' | 'enviado'
                attempt_id=attempt_id,  # si en_progreso o enviado
                intento_nro=intento_nro,
                expires_at=exp_at,
            )
        )

    # scope=selected → ocultar los 'pendiente'
    if scope == "selected":
        items = [it for it in items if it.estado != "pendiente"]

    # Summary (recalcular siempre sobre la lista final)
    summary = {"pendiente": 0, "en_progreso": 0, "enviado": 0}
    for it in items:
        if it.estado in summary:
            summary[it.estado] += 1

    return QueueOut(survey_id=survey_id, summary=summary, items=items)
