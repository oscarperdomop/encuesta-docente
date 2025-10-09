# encuesta-docente/api/app/api/v1/endpoints/attempts.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import Response as FastAPIResponse
from sqlalchemy import func, or_, and_, MetaData, Table, select
from sqlalchemy.orm import Session

from app.core.security import (
    get_current_user,
    get_current_user_with_claims,  # si lo usas en otros lados; aquí no se usa
    get_admin_user,
)
from app.db.session import get_db
from app.models.encuesta import Survey, Question, SurveySection
from app.models.docente import Teacher, SurveyTeacherAssignment
from app.models.attempt import Attempt, Response as AttemptResponse
# ❌ IMPORTANTE: NO importamos AttemptLimit para evitar selects con columnas inexistentes
from app.models.attempt_limit import AttemptLimit
from app.schemas.attempts import (
    AttemptsCreateIn,
    AttemptOut,
    AttemptPatchIn,
    SubmitIn,
    SubmitOut,
    NextItemOut,
)

router = APIRouter(tags=["attempts"])

# Producción: 30 min (en pruebas 1 min)
ATTEMPT_TIMEOUT_MIN = 30
# Base de sesiones permitidas por usuario x encuesta (si no hay fila en attempt_limits)
BASE_MAX_SESSIONS = 2
# Límite de docentes por creación en lote (no usado aquí, pero útil tenerlo)
MAX_DOCENTES_POR_CREACION = 20


# -------------------- helpers -------------------- #

def _attempt_limits_table(db: Session) -> Table:
    """Refleja la tabla attempt_limits EXACTAMENTE como está en BD."""
    meta = MetaData()
    return Table("attempt_limits", meta, autoload_with=db.get_bind())

def _max_permitidos(db: Session, survey_id: UUID, user_id: UUID) -> int:
    """
    max_intentos + extra_otorgados desde attempt_limits.
    Si no hay fila: base = BASE_MAX_SESSIONS.
    """
    row = (
        db.query(AttemptLimit)
        .filter(AttemptLimit.survey_id == survey_id, AttemptLimit.user_id == user_id)
        .first()
    )
    base = row.max_intentos if row and row.max_intentos is not None else BASE_MAX_SESSIONS
    extra = row.extra_otorgados if row else 0
    return int(base) + int(extra)

# Si tienes funciones duplicadas, deja un alias para evitar inconsistencias:
def _get_max_sessions(db: Session, survey_id: UUID, user_id: UUID) -> int:
    return _max_permitidos(db, survey_id, user_id)

def _max_sessions_for_user(db: Session, survey_id: UUID, user_id: UUID) -> int:
    return _max_permitidos(db, survey_id, user_id)

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

def _expire_if_token_rolled(db: Session, survey_id: UUID, user_id: UUID, token_iat: int | None) -> bool:
    """
    Si el usuario renovó sesión (nuevo JWT con iat más reciente) mientras había intentos EN_PROGRESO,
    los expira para evitar reusar sesiones viejas.
    """
    if not token_iat:
        return False
    token_iat_dt = datetime.fromtimestamp(int(token_iat), tz=timezone.utc)
    now = datetime.now(timezone.utc)

    first_active = (
        db.query(Attempt)
        .filter(
            Attempt.survey_id == survey_id,
            Attempt.user_id == user_id,
            Attempt.estado == "en_progreso",
            or_(Attempt.expires_at.is_(None), Attempt.expires_at > now),
        )
        .order_by(Attempt.id.asc().nullslast())
        .first()
    )
    if first_active and first_active.creado_en and token_iat_dt > first_active.creado_en:
        db.query(Attempt).filter(
            Attempt.survey_id == survey_id,
            Attempt.user_id == user_id,
            Attempt.estado == "en_progreso",
        ).update({Attempt.estado: "expirado"}, synchronize_session=False)
        db.commit()
        return True
    return False

def _count_failures(db: Session, survey_id: UUID, user_id: UUID) -> int:
    return (
        db.query(func.count(Attempt.id))
        .filter(
            Attempt.survey_id == survey_id,
            Attempt.user_id == user_id,
            Attempt.estado.in_(["fallido", "expirado"]),
        )
        .scalar()
    ) or 0

def _active_session_nro(db: Session, survey_id: UUID, user_id: UUID, now: datetime) -> int | None:
    """Devuelve el intento_nro de la sesión activa (en_progreso no expirada), si existe."""
    return db.query(func.max(Attempt.intento_nro)).filter(
        Attempt.survey_id == survey_id,
        Attempt.user_id == user_id,
        Attempt.estado == "en_progreso",
        or_(Attempt.expires_at.is_(None), Attempt.expires_at > now),
    ).scalar()

def _max_session_nro(db: Session, survey_id: UUID, user_id: UUID) -> int:
    """Máximo intento_nro histórico (0 si no hay)."""
    val = db.query(func.max(Attempt.intento_nro)).filter(
        Attempt.survey_id == survey_id,
        Attempt.user_id == user_id,
    ).scalar()
    return int(val or 0)

def _count_used_sessions(db: Session, survey_id: UUID, user_id: UUID) -> int:
    """
    Cuenta SESIONES usadas (DISTINCT intento_nro) que terminaron en 'expirado' o 'fallido'.
    Evita sobrecontar por cantidad de docentes en esa sesión.
    """
    return int((
        db.query(func.count(func.distinct(Attempt.intento_nro)))
        .filter(
            Attempt.survey_id == survey_id,
            Attempt.user_id == user_id,
            Attempt.estado.in_(["expirado", "fallido"]),
        )
        .scalar()
    ) or 0)


# -------------------- endpoints -------------------- #

@router.get("/attempts/summary")
def attempts_summary(
    survey_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    user_id = _extract_user_id(current)

    # 1) Expira intentos en_progreso que ya vencieron
    _expire_stale_attempts(db, survey_id, user_id)

    # 2) Conteos por estado (para la UI)
    rows = (
        db.query(Attempt.estado, func.count(Attempt.id))
        .filter(Attempt.survey_id == survey_id, Attempt.user_id == user_id)
        .group_by(Attempt.estado)
        .all()
    )
    counts = {estado: n for estado, n in rows}

    now = datetime.now(timezone.utc)

    # 3) Nro de sesión activa (si hay en_progreso vigente)
    intento_activo = _active_session_nro(db, survey_id, user_id, now)
    ultimo_intento = _max_session_nro(db, survey_id, user_id)

    # 4) Sesiones usadas (expirado/fallido)
    used_sessions = _count_used_sessions(db, survey_id, user_id)

    max_permitidos = _get_max_sessions(db, survey_id, user_id)
    restantes = max(0, max_permitidos - used_sessions)

    # 5) Vencimiento de la sesión abierta (para countdown en UI)
    open_exp = (
        db.query(func.max(Attempt.expires_at))
        .filter(
            Attempt.survey_id == survey_id,
            Attempt.user_id == user_id,
            Attempt.estado == "en_progreso",
            or_(Attempt.expires_at.is_(None), Attempt.expires_at > now),
        )
        .scalar()
    )
    has_open = bool(intento_activo and (open_exp is None or open_exp > now))

    return {
        "survey_id": str(survey_id),
        "intento_activo": intento_activo,
        "ultimo_intento": ultimo_intento,
        "max_permitidos": max_permitidos,
        "usadas": used_sessions,
        "restantes": restantes,
        "has_open_session": has_open,
        "open_session_expires_at": open_exp,
        "estados": {
            "en_progreso": counts.get("en_progreso", 0),
            "enviado": counts.get("enviado", 0),
            "expirado": counts.get("expirado", 0),
            "fallido": counts.get("fallido", 0),
        },
    }


@router.get("/attempts/next", response_model=NextItemOut)
def get_next(
    survey_id: UUID = Query(..., description="ID de la encuesta"),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """Devuelve el attempt EN_PROGRESO que vence antes. Si no hay, 204."""
    user_id = _extract_user_id(current)

    # Expirar los vencidos antes de decidir
    _expire_stale_attempts(db, survey_id, user_id)

    now = datetime.now(timezone.utc)

    row = (
        db.query(Attempt, Teacher.nombre.label("teacher_nombre"))
        .join(Teacher, Teacher.id == Attempt.teacher_id)
        .filter(
            Attempt.survey_id == survey_id,
            Attempt.user_id == user_id,
            Attempt.estado == "en_progreso",
            or_(Attempt.expires_at.is_(None), Attempt.expires_at > now),
        )
        .order_by(
            Attempt.expires_at.asc().nullslast(),
            Attempt.intento_nro.asc(),
            Attempt.id.asc(),
        )
        .first()
    )

    if not row:
        return FastAPIResponse(status_code=204)  # No Content

    att, tname = row
    return NextItemOut(
        survey_id=survey_id,
        teacher_id=att.teacher_id,
        teacher_nombre=tname,
        attempt_id=att.id,
        expires_at=att.expires_at,
        intento_nro=att.intento_nro,
    )


@router.get("/attempts/quota")
def get_attempts_quota(
    survey_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    user_id = _extract_user_id(current)

    _expire_stale_attempts(db, survey_id, user_id)

    max_permitidos = _max_permitidos(db, survey_id, user_id)
    counts = dict(
        db.query(Attempt.estado, func.count(Attempt.id))
        .filter(Attempt.survey_id == survey_id, Attempt.user_id == user_id)
        .group_by(Attempt.estado)
        .all()
    )
    fallidos = (counts.get("fallido", 0) or 0) + (counts.get("expirado", 0) or 0)
    restantes = max(0, max_permitidos - fallidos)
    return {
        "survey_id": str(survey_id),
        "max_permitidos": max_permitidos,
        "fallidos": fallidos,
        "restantes": restantes,
    }


@router.get("/attempts", response_model=list[AttemptOut])
def list_attempts(
    survey_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    user_id = _extract_user_id(current)
    q = db.query(Attempt).filter(Attempt.user_id == user_id)
    if survey_id:
        _expire_stale_attempts(db, survey_id, user_id)
        q = q.filter(Attempt.survey_id == survey_id)
    rows = q.all()
    return [
        AttemptOut(
            id=r.id,
            survey_id=r.survey_id,
            teacher_id=r.teacher_id,
            estado=r.estado,
            intento_nro=r.intento_nro,
            expires_at=r.expires_at,
        )
        for r in rows
    ]


@router.post("/attempts", response_model=list[AttemptOut], status_code=201)
def create_attempts(payload: AttemptsCreateIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    user_id = _extract_user_id(current)

    survey = db.query(Survey).filter(Survey.id == payload.survey_id, Survey.estado == "activa").first()
    if not survey:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada o inactiva")

    # expira antes de contar
    _expire_stale_attempts(db, survey_id=payload.survey_id, user_id=user_id)

    fails = _count_failures(db, survey_id=payload.survey_id, user_id=user_id)
    max_permitidos = _max_permitidos(db, payload.survey_id, user_id)
    if fails >= max_permitidos:
        raise HTTPException(status_code=403, detail="Límite de intentos fallidos alcanzado")

    valid_teacher_ids = {
        tid
        for (tid,) in (
            db.query(Teacher.id)
            .join(SurveyTeacherAssignment, SurveyTeacherAssignment.teacher_id == Teacher.id)
            .filter(
                SurveyTeacherAssignment.survey_id == payload.survey_id,
                Teacher.estado == "activo",
            )
            .all()
        )
    }
    for tid in payload.teacher_ids:
        if tid not in valid_teacher_ids:
            raise HTTPException(status_code=400, detail=f"Docente {tid} no pertenece a la encuesta")

    intento_nro = fails + 1
    expires = datetime.now(timezone.utc) + timedelta(minutes=ATTEMPT_TIMEOUT_MIN)
    now = datetime.now(timezone.utc)

    created: list[Attempt] = []
    for tid in payload.teacher_ids:
        already_sent = (
            db.query(Attempt.id)
            .filter(
                Attempt.survey_id == payload.survey_id,
                Attempt.user_id == user_id,
                Attempt.teacher_id == tid,
                Attempt.estado == "enviado",
            )
            .first()
        )
        if already_sent:
            raise HTTPException(status_code=409, detail=f"Docente {tid} ya fue evaluado por este usuario")

        existing = (
            db.query(Attempt)
            .filter(
                Attempt.survey_id == payload.survey_id,
                Attempt.user_id == user_id,
                Attempt.teacher_id == tid,
                Attempt.estado == "en_progreso",
                or_(Attempt.expires_at.is_(None), Attempt.expires_at > now),
            )
            .first()
        )
        if existing:
            created.append(existing)
            continue

        stale = (
            db.query(Attempt)
            .filter(
                Attempt.survey_id == payload.survey_id,
                Attempt.user_id == user_id,
                Attempt.teacher_id == tid,
                Attempt.estado == "en_progreso",
                Attempt.expires_at.isnot(None),
                Attempt.expires_at <= now,
            )
            .update({Attempt.estado: "expirado"}, synchronize_session=False)
        )
        if stale:
            db.commit()
            fails = _count_failures(db, payload.survey_id, user_id)
            if fails >= _max_permitidos(db, payload.survey_id, user_id):
                raise HTTPException(status_code=403, detail="Límite de intentos fallidos alcanzado")
            intento_nro = fails + 1

        att = Attempt(
            survey_id=payload.survey_id,
            user_id=user_id,
            teacher_id=tid,
            intento_nro=intento_nro,
            estado="en_progreso",
            expires_at=expires,
        )
        db.add(att)
        created.append(att)

    db.commit()
    for att in created:
        db.refresh(att)

    return [
        AttemptOut(
            id=att.id,
            survey_id=att.survey_id,
            teacher_id=att.teacher_id,
            estado=att.estado,
            intento_nro=att.intento_nro,
            expires_at=att.expires_at,
        )
        for att in created
    ]


@router.patch("/attempts/{attempt_id}", response_model=AttemptOut)
def patch_attempt(
    attempt_id: UUID,
    payload: AttemptPatchIn,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    user_id = _extract_user_id(current)
    att = db.query(Attempt).filter(Attempt.id == attempt_id, Attempt.user_id == user_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attempt no encontrado")
    if att.estado != "en_progreso":
        raise HTTPException(status_code=409, detail=f"No editable en estado {att.estado}")

    if payload.progreso is not None:
        att.progreso_json = payload.progreso
    if payload.renew is None or payload.renew:
        att.expires_at = datetime.now(timezone.utc) + timedelta(minutes=ATTEMPT_TIMEOUT_MIN)

    db.commit()
    db.refresh(att)
    return AttemptOut(
        id=att.id,
        survey_id=att.survey_id,
        teacher_id=att.teacher_id,
        estado=att.estado,
        intento_nro=att.intento_nro,
        expires_at=att.expires_at,
    )


@router.post("/attempts/{attempt_id}/submit", response_model=SubmitOut)
def submit_attempt(
    attempt_id: UUID,
    payload: SubmitIn,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    user_id = _extract_user_id(current)

    att = db.query(Attempt).filter(Attempt.id == attempt_id, Attempt.user_id == user_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attempt no encontrado")
    if att.estado == "enviado":
        raise HTTPException(status_code=409, detail="Attempt ya fue enviado")
    if att.expires_at and datetime.now(timezone.utc) > att.expires_at:
        att.estado = "expirado"
        db.commit()
        raise HTTPException(status_code=409, detail="Attempt expirado (30 min)")

    # Preguntas
    qs = db.query(Question).filter(Question.survey_id == att.survey_id).all()
    likert_qs = [q for q in qs if (q.tipo or "").lower() == "likert"]
    if len(likert_qs) != 15:
        raise HTTPException(status_code=500, detail="Se esperaban 15 preguntas Likert")

    likert_ids = {q.id for q in likert_qs}
    provided_ids = {a.question_id for a in payload.answers}
    missing = likert_ids - provided_ids
    if missing:
        raise HTTPException(status_code=400, detail=f"Faltan respuestas a preguntas: {sorted(list(missing))}")

    # Limpiar e insertar
    db.query(AttemptResponse).filter(AttemptResponse.attempt_id == att.id).delete(synchronize_session=False)
    for a in payload.answers:
        v = int(a.value)
        if v not in (1, 2, 3, 4, 5):
            raise HTTPException(status_code=400, detail=f"Valor inválido {a.value} en pregunta {a.question_id}")
        db.add(AttemptResponse(attempt_id=att.id, question_id=a.question_id, valor_likert=v))

    # Q16 opcional
    q16 = next((q for q in qs if q.codigo == "Q16"), None)
    if q16 and payload.q16 and (payload.q16.positivos or payload.q16.mejorar or payload.q16.comentarios):
        db.add(AttemptResponse(attempt_id=att.id, question_id=q16.id, texto=payload.q16.model_dump()))

    # Scoring
    pesos = {q.id: (q.peso or 1) for q in likert_qs}
    sum_w = sum(pesos.values())
    sum_wx = sum(int(a.value) * pesos[a.question_id] for a in payload.answers)
    total_score = round(sum_wx / sum_w, 3) if sum_w else None

    sections = db.query(SurveySection).filter(SurveySection.survey_id == att.survey_id).all()
    sec_scores = []
    for sec in sections:
        sec_q_ids = [q.id for q in likert_qs if q.section_id == sec.id]
        if not sec_q_ids:
            continue
        sec_w = sum(pesos[qid] for qid in sec_q_ids)
        sec_wx = sum(
            next((int(a.value) * pesos[a.question_id] for a in payload.answers if a.question_id == qid), 0)
            for qid in sec_q_ids
        )
        sec_scores.append({"section_id": sec.id, "titulo": sec.titulo, "score": round(sec_wx / sec_w, 3)})

    att.estado = "enviado"
    db.commit()

    return SubmitOut(estado="enviado", scores={"total": total_score, "secciones": sec_scores})


@router.get("/attempts/{attempt_id}")
def get_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    user_id = _extract_user_id(current)
    att = db.query(Attempt).filter(Attempt.id == attempt_id, Attempt.user_id == user_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attempt no encontrado")
    res = db.query(AttemptResponse).filter(AttemptResponse.attempt_id == attempt_id).all()
    return {
        "id": att.id,
        "survey_id": att.survey_id,
        "teacher_id": att.teacher_id,
        "estado": att.estado,
        "expires_at": att.expires_at,
        "answers": [
            {"question_id": r.question_id, "value": r.valor_likert, "texto": r.texto}
            for r in res
        ],
    }


@router.post("/attempts/admin/reset")
def reset_attempts(
    survey_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current=Depends(get_admin_user),
):
    db.query(Attempt).filter(
        Attempt.survey_id == survey_id,
        Attempt.user_id == user_id,
        Attempt.estado.in_(["expirado", "fallido"]),
    ).delete(synchronize_session=False)
    db.commit()
    return {"ok": True}


@router.get("/attempts/current")
def get_current_attempt(
    survey_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    user_id = _extract_user_id(current)

    # Expira primero lo vencido
    _expire_stale_attempts(db, survey_id, user_id)

    now = datetime.now(timezone.utc)
    att = (
        db.query(Attempt)
        .filter(
            Attempt.survey_id == survey_id,
            Attempt.user_id == user_id,
            Attempt.estado == "en_progreso",
            or_(Attempt.expires_at.is_(None), Attempt.expires_at > now),
        )
        .order_by(Attempt.id.asc().nullslast())  # el más antiguo vigente
        .first()
    )
    if not att:
        return {"status": "empty"}  # no hay nadie en progreso

    teacher = db.query(Teacher).filter(Teacher.id == att.teacher_id).first()
    return {
        "attempt_id": att.id,
        "teacher_id": att.teacher_id,
        "teacher_nombre": teacher.nombre if teacher else None,
        "expires_at": att.expires_at,
        "intento_nro": att.intento_nro,
    }
