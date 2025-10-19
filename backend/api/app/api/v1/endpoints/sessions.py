from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.turno import Turno
from app.models.attempt import Attempt
from app.schemas.sessions import SessionCloseOut

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Valor por defecto si no está definido en settings/.env
MAX_TURNOS = getattr(settings, "MAX_TURNOS", 2)


# ----------------------- helpers -----------------------

def _get_open_turno(db: Session, user_id: UUID) -> Optional[Turno]:
    """Devuelve el último turno abierto del usuario (si existe)."""
    return (
        db.query(Turno)
        .filter(Turno.user_id == user_id, Turno.status == "open")
        .order_by(Turno.opened_at.desc())
        .first()
    )

def _close_latest_open_turno(db: Session, user_id: UUID) -> bool:
    """Cierra el último turno abierto del usuario si existe. Devuelve True si lo cerró."""
    t = _get_open_turno(db, user_id)
    if not t:
        return False
    if t.status != "closed":
        t.status = "closed"
        t.closed_at = func.now()
        db.add(t)
        db.commit()
    return True

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


# ----------------------- endpoints de sesión por encuesta -----------------------

@router.post("/close", response_model=SessionCloseOut)
def close_session(
    survey_id: UUID = Query(..., description="ID de la encuesta a cerrar"),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """
    Cierra el 'turno' lógico del usuario para esa encuesta si NO hay attempts en_progreso.
    Además, si no hay intentos en progreso, cierra el turno abierto del usuario.
    """
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

    if en_progreso > 0:
        raise HTTPException(
            status_code=409,
            detail="Aún tienes docentes en progreso. Termina o deja expirar antes de cerrar el turno."
        )

    # 3) Cerrar el turno abierto (si lo hubiera)
    _close_latest_open_turno(db, user_id)

    return SessionCloseOut(
        survey_id=survey_id,
        closed=True,
        enviados=enviados,
        en_progreso=en_progreso,
        expirados=expirados,
        fallidos=fallidos,
        closed_at=datetime.now(timezone.utc),
    )


# ----------------------- endpoints de 'turno' -----------------------

@router.get("/turno/current")
def turno_current(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Devuelve el turno abierto actual (si existe) y el remanente de cupo.
    Respuesta: { turno_id: str | None, remaining: int }
    """
    t = _get_open_turno(db, user.id)
    used = db.query(func.count(Turno.id)).filter(Turno.user_id == user.id).scalar() or 0
    remaining = max(0, MAX_TURNOS - used)
    return {"turno_id": str(t.id) if t else None, "remaining": remaining}

@router.post("/turno/open")
def open_turno(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
    user_agent: Optional[str] = Header(None, alias="User-Agent"),
    x_forwarded_for: Optional[str] = Header(None, alias="X-Forwarded-For"),
):
    """
    Abre un turno para el usuario autenticado respetando el tope MAX_TURNOS.
    - Si ya hay un turno 'open', lo reutiliza (idempotente).
    """
    existing = _get_open_turno(db, user.id)
    if existing:
        used = db.query(func.count(Turno.id)).filter(Turno.user_id == user.id).scalar() or 0
        remaining = max(0, MAX_TURNOS - used)
        return {"turno_id": str(existing.id), "remaining": remaining}

    used = db.query(func.count(Turno.id)).filter(Turno.user_id == user.id).scalar() or 0
    if used >= MAX_TURNOS:
        raise HTTPException(status_code=403, detail=f"Has agotado tus {MAX_TURNOS} turnos.")

    t = Turno(user_id=user.id, status="open", opened_at=func.now())
    db.add(t)
    db.commit()
    db.refresh(t)

    remaining = max(0, MAX_TURNOS - (used + 1))
    return {"turno_id": str(t.id), "remaining": remaining}

@router.post("/turno/close")
def close_turno(
    x_turno_id: Optional[str] = Header(None, alias="X-Turno-Id"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Cierra el turno explícitamente (capa extra; no confundir con /sessions/close por encuesta).
    """
    if not x_turno_id:
        raise HTTPException(status_code=400, detail="Falta header X-Turno-Id.")
    t = db.query(Turno).filter(Turno.id == x_turno_id, Turno.user_id == user.id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado.")
    if t.status != "closed":
        t.status = "closed"
        t.closed_at = func.now()
        db.add(t)
        db.commit()
    return {"ok": True}

@router.get("/turno/quota")
def turno_quota(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    used = db.query(func.count(Turno.id)).filter(Turno.user_id == user.id).scalar() or 0
    remaining = max(0, MAX_TURNOS - used)
    return {"used": used, "limit": MAX_TURNOS, "remaining": remaining}


# -------- Dependency para proteger endpoints --------
def require_turno_open(
    x_turno_id: Optional[str] = Header(None, alias="X-Turno-Id"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
) -> Turno:
    if not x_turno_id:
        raise HTTPException(status_code=403, detail="Turno no iniciado (falta X-Turno-Id).")
    t = db.query(Turno).filter(
        Turno.id == x_turno_id, Turno.user_id == user.id, Turno.status == "open"
    ).first()
    if not t:
        raise HTTPException(status_code=403, detail="Turno inválido o cerrado.")
    return t
