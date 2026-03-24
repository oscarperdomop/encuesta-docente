from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import get_admin_user
from app.db.session import get_db
from app.models.docente import Teacher
from app.schemas.admin import (
    AssignTeachersIn,
    AssignTeachersOut,
    QuestionOut,
    UpdateQuestionWeightIn,
)

router = APIRouter(tags=["admin"])

MAX_ASSIGN_BULK = 500


@router.post("/admin/surveys/{survey_id}/teachers/assign", response_model=AssignTeachersOut, status_code=200)
def admin_assign_teachers(
    survey_id: UUID = Path(..., description="ID de la encuesta"),
    payload: AssignTeachersIn = ...,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user),
):
    # 1) Validaciones basicas
    survey = db.execute(
        text(
            """
            SELECT id, estado
            FROM public.surveys
            WHERE id = :sid
            """
        ),
        {"sid": str(survey_id)},
    ).mappings().first()
    if not survey:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    if (survey.get("estado") or "").lower() != "activa":
        raise HTTPException(status_code=409, detail="Solo se permiten asignaciones en encuestas activas")

    if not payload.teacher_ids:
        raise HTTPException(status_code=400, detail="Debe enviar al menos un teacher_id")
    if len(payload.teacher_ids) > MAX_ASSIGN_BULK:
        raise HTTPException(status_code=400, detail=f"Maximo {MAX_ASSIGN_BULK} docentes por operacion")

    # Normaliza: dedup conservando orden
    seen = set()
    teacher_ids: list[UUID] = []
    for tid in payload.teacher_ids:
        if tid not in seen:
            seen.add(tid)
            teacher_ids.append(tid)

    # 2) Validar que existan y esten activos
    active_map = {
        t.id
        for t in db.query(Teacher.id).filter(Teacher.id.in_(teacher_ids), Teacher.estado == "activo").all()
    }
    missing = [str(t) for t in teacher_ids if t not in active_map]
    if missing:
        raise HTTPException(status_code=400, detail=f"Docentes invalidos/inactivos: {missing}")

    # 3) Cargar asignaciones actuales
    current_rows = db.execute(
        text(
            """
            SELECT teacher_id
            FROM public.survey_teacher_assignments
            WHERE survey_id = :sid
            """
        ),
        {"sid": str(survey_id)},
    ).all()
    current_set = {row[0] for row in current_rows}

    mode: Literal["add", "remove", "set"] = payload.mode or "add"
    desired_set = set(teacher_ids)
    to_add: set[UUID] = set()
    to_remove: set[UUID] = set()

    if mode == "add":
        to_add = desired_set - current_set
    elif mode == "remove":
        to_remove = desired_set & current_set
    elif mode == "set":
        to_add = desired_set - current_set
        to_remove = current_set - desired_set
    else:
        raise HTTPException(status_code=400, detail="mode invalido (use add | remove | set)")

    # 4) Ejecutar cambios (SQL directo para compatibilidad de tipos UUID)
    for tid in to_add:
        db.execute(
            text(
                """
                INSERT INTO public.survey_teacher_assignments (survey_id, teacher_id)
                SELECT CAST(:sid AS uuid), CAST(:tid AS uuid)
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM public.survey_teacher_assignments
                    WHERE survey_id = CAST(:sid AS uuid)
                      AND teacher_id = CAST(:tid AS uuid)
                )
                """
            ),
            {"sid": str(survey_id), "tid": str(tid)},
        )

    for tid in to_remove:
        db.execute(
            text(
                """
                DELETE FROM public.survey_teacher_assignments
                WHERE survey_id = :sid AND teacher_id = :tid
                """
            ),
            {"sid": str(survey_id), "tid": str(tid)},
        )

    db.commit()

    # 5) Resultado final
    final_count = int(
        db.execute(
            text(
                """
                SELECT COUNT(*) AS n
                FROM public.survey_teacher_assignments
                WHERE survey_id = :sid
                """
            ),
            {"sid": str(survey_id)},
        ).scalar()
        or 0
    )

    if mode == "add":
        unchanged = len(desired_set & current_set)
    elif mode == "remove":
        unchanged = len(desired_set - current_set)
    else:  # set
        unchanged = len(desired_set & current_set)

    return AssignTeachersOut(
        survey_id=survey_id,
        mode=mode,
        before=len(current_set),
        after=final_count,
        added=len(to_add),
        removed=len(to_remove),
        unchanged=unchanged,
    )


@router.put("/admin/surveys/{survey_id}/questions/{question_id}", response_model=QuestionOut, status_code=200)
def admin_update_question_weight(
    survey_id: UUID = Path(..., description="ID de la encuesta"),
    question_id: UUID = Path(..., description="ID de la pregunta de la encuesta"),
    payload: UpdateQuestionWeightIn = ...,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user),
):
    if payload.peso is None:
        raise HTTPException(status_code=400, detail="Debe enviar 'peso'")
    if payload.peso <= 0:
        raise HTTPException(status_code=400, detail="El peso debe ser > 0")

    qrow = db.execute(
        text(
            """
            SELECT id, survey_id, section_id, codigo, enunciado, tipo, orden, peso
            FROM public.questions
            WHERE id = :qid AND survey_id = :sid
            """
        ),
        {"qid": str(question_id), "sid": str(survey_id)},
    ).mappings().first()
    if not qrow:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada en esta encuesta")

    db.execute(
        text(
            """
            UPDATE public.questions
            SET peso = :peso
            WHERE id = :qid AND survey_id = :sid
            """
        ),
        {"peso": float(payload.peso), "qid": str(question_id), "sid": str(survey_id)},
    )
    db.commit()

    return QuestionOut(
        id=qrow["id"],
        survey_id=qrow["survey_id"],
        section_id=qrow["section_id"],
        codigo=qrow["codigo"],
        enunciado=qrow["enunciado"],
        tipo=qrow["tipo"],
        orden=int(qrow["orden"]),
        peso=float(payload.peso),
    )
