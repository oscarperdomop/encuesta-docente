# api/app/api/v1/endpoints/admin_surveys.py
from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.security import get_admin_user
from app.db.session import get_db
from app.models.docente import Teacher, SurveyTeacherAssignment
from app.models.encuesta import Survey, Question
from app.schemas.admin import (
    AssignTeachersIn,
    AssignTeachersOut,
    UpdateQuestionWeightIn,
    QuestionOut,
)

router = APIRouter(tags=["admin"])

MAX_ASSIGN_BULK = 500


# --------------------------
# POST /admin/surveys/{survey_id}/teachers/assign
# --------------------------
@router.post("/admin/surveys/{survey_id}/teachers/assign", response_model=AssignTeachersOut, status_code=200)
def admin_assign_teachers(
    survey_id: UUID = Path(..., description="ID de la encuesta"),
    payload: AssignTeachersIn = ...,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user),
):
    # 1) Validaciones básicas
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")

    if not payload.teacher_ids:
        raise HTTPException(status_code=400, detail="Debe enviar al menos un teacher_id")

    if len(payload.teacher_ids) > MAX_ASSIGN_BULK:
        raise HTTPException(status_code=400, detail=f"Máximo {MAX_ASSIGN_BULK} docentes por operación")

    # Normaliza: dedup conservando orden
    seen = set()
    teacher_ids = []
    for tid in payload.teacher_ids:
        if tid not in seen:
            seen.add(tid)
            teacher_ids.append(tid)

    # 2) Validar que existan y estén activos
    active_map = {t.id for t in db.query(Teacher.id).filter(Teacher.id.in_(teacher_ids), Teacher.estado == "activo").all()}
    missing = [str(t) for t in teacher_ids if t not in active_map]
    if missing:
        raise HTTPException(status_code=400, detail=f"Docentes inválidos/inactivos: {missing}")

    # 3) Cargar asignaciones actuales
    current_set = {
        t_id
        for (t_id,) in db.query(SurveyTeacherAssignment.teacher_id)
        .filter(SurveyTeacherAssignment.survey_id == survey_id)
        .all()
    }

    mode: Literal["add", "remove", "set"] = payload.mode or "add"

    to_add, to_remove = set(), set()
    if mode == "add":
        to_add = set(teacher_ids) - current_set
    elif mode == "remove":
        to_remove = set(teacher_ids) & current_set
    elif mode == "set":
        desired = set(teacher_ids)
        to_add = desired - current_set
        to_remove = current_set - desired
    else:
        raise HTTPException(status_code=400, detail="mode inválido (use add | remove | set)")

    # 4) Ejecutar cambios
    added = 0
    removed = 0

    if to_add:
        for tid in to_add:
            db.add(SurveyTeacherAssignment(survey_id=survey_id, teacher_id=tid))
        added = len(to_add)

    if to_remove:
        removed = (
            db.query(SurveyTeacherAssignment)
            .filter(
                SurveyTeacherAssignment.survey_id == survey_id,
                SurveyTeacherAssignment.teacher_id.in_(list(to_remove)),
            )
            .delete(synchronize_session=False)
        )

    db.commit()

    # 5) Resultado final
    final_count = db.query(SurveyTeacherAssignment).filter(SurveyTeacherAssignment.survey_id == survey_id).count()
    return AssignTeachersOut(
        survey_id=survey_id,
        mode=mode,
        before=len(current_set),
        after=final_count,
        added=added,
        removed=removed,
        unchanged=final_count - added,  # solo informativo
    )


# --------------------------
# PUT /admin/surveys/{survey_id}/questions/{question_id}
# --------------------------
@router.put("/admin/surveys/{survey_id}/questions/{question_id}", response_model=QuestionOut, status_code=200)
def admin_update_question_weight(
    survey_id: UUID = Path(..., description="ID de la encuesta"),
    question_id: UUID = Path(..., description="ID de la pregunta de la encuesta"),
    payload: UpdateQuestionWeightIn = ...,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user),
):
    # 1) Verificar pregunta pertenece a la encuesta
    q = db.query(Question).filter(Question.id == question_id, Question.survey_id == survey_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada en esta encuesta")

    # 2) Validar y aplicar peso
    if payload.peso is None:
        raise HTTPException(status_code=400, detail="Debe enviar 'peso'")
    if payload.peso <= 0:
        raise HTTPException(status_code=400, detail="El peso debe ser > 0")

    q.peso = float(payload.peso)
    db.commit()
    db.refresh(q)

    return QuestionOut(
        id=q.id,
        survey_id=q.survey_id,
        section_id=q.section_id,
        codigo=q.codigo,
        enunciado=q.enunciado,
        tipo=q.tipo,
        orden=q.orden,
        peso=q.peso,
    )
