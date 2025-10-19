# api/app/api/v1/endpoints/catalogs.py
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import text, or_

from app.db.session import get_db
from app.models.encuesta import Survey, SurveySection, Question
from app.models.docente import Teacher, SurveyTeacherAssignment
from app.schemas.teacher import TeacherOut
from app.core.security import get_current_user  # 👈 necesario para saber el usuario

router = APIRouter(tags=["catalogs"])

# ✅ LISTAR ENCUESTAS ACTIVAS
@router.get("/surveys/activas")
def listar_encuestas_activas(
    hoy: date | None = Query(None, description="Filtra por vigencia en esta fecha (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT id, codigo, nombre, estado, fecha_inicio, fecha_fin
        FROM public.surveys
        WHERE estado = 'activa'
          AND (
            :hoy IS NULL
            OR (
              (fecha_inicio IS NULL OR fecha_inicio <= :hoy)
              AND (fecha_fin IS NULL OR fecha_fin >= :hoy)
            )
          )
        ORDER BY fecha_inicio NULLS FIRST, nombre
    """)
    rows = db.execute(sql, {"hoy": hoy}).mappings().all()
    return rows


@router.get("/surveys/{survey_id}/questions")
def listar_preguntas(
    survey_id: UUID,  # <-- aquí el cambio
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT q.id, q.codigo, q.enunciado, q.orden, q.tipo, q.peso,
               s.titulo AS section
        FROM public.questions q
        JOIN public.survey_sections s ON s.id = q.section_id
        WHERE q.survey_id = :sid
        ORDER BY q.orden
    """)
    rows = db.execute(sql, {"sid": str(survey_id)}).mappings().all()
    return rows

@router.get("/surveys/by-codigo/{codigo}")
def survey_by_codigo(codigo: str, db: Session = Depends(get_db)):
    s = db.query(Survey).filter(Survey.codigo==codigo).first()
    if not s:
        raise HTTPException(404, "Encuesta no encontrada")
    return s


@router.get("/surveys/{survey_id}/teachers")
def listar_docentes_de_encuesta(
    survey_id: UUID = Path(...),
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    hide_evaluated: bool = Query(False, description="Oculta docentes ya evaluados por el usuario actual"),
    include_state: bool = Query(True, description="Incluye columna booleana 'evaluated'"),
    db: Session = Depends(get_db),
    current = Depends(get_current_user),
):
    """
    Lista docentes asignados a la encuesta.

    - hide_evaluated=true  -> oculta docentes ya 'enviado' por el usuario actual.
    - include_state=true   -> agrega columna booleana 'evaluated' por fila.
    """
    # (opcional) validar encuesta activa
    survey = db.query(Survey).filter(Survey.id == survey_id, Survey.estado == "activa").first()
    if not survey:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada o inactiva")

    # id del usuario desde el token
    user_id = getattr(current, "id", None) or current.get("sub") or current.get("id")

    # SELECT dinámico: añadimos 'evaluated' sólo si include_state = true
    select_head = """
        SELECT t.id, t.identificador, t.nombre, t.programa, t.estado
    """
    evaluated_expr = """
        , EXISTS (
            SELECT 1
            FROM public.attempts a
            WHERE a.survey_id = :sid
              AND a.user_id   = :uid
              AND a.teacher_id = t.id
              AND a.estado = 'enviado'
        ) AS evaluated
    """
    if include_state:
        select_head += evaluated_expr

    base_sql = f"""
        {select_head}
        FROM public.survey_teacher_assignments sta
        JOIN public.teachers t ON t.id = sta.teacher_id
        WHERE sta.survey_id = :sid
          AND (
            :q IS NULL OR
            t.nombre ILIKE '%' || :q || '%' OR
            t.identificador ILIKE '%' || :q || '%' OR
            COALESCE(t.programa, '') ILIKE '%' || :q || '%'
          )
    """

    # Si hide_evaluated = true, filtramos con NOT EXISTS
    if hide_evaluated:
        base_sql += """
          AND NOT EXISTS (
            SELECT 1
            FROM public.attempts a2
            WHERE a2.survey_id = :sid
              AND a2.user_id   = :uid
              AND a2.teacher_id = t.id
              AND a2.estado = 'enviado'
          )
        """

    base_sql += """
        ORDER BY t.nombre
        LIMIT :limit OFFSET :offset
    """

    params = {
        "sid": str(survey_id),
        "uid": str(user_id),
        "q": q,
        "limit": limit,
        "offset": offset,
    }

    rows = db.execute(text(base_sql), params).mappings().all()

    # Para mantener forma homogénea, si include_state=false añadimos evaluated=false
    if not include_state:
        out = []
        for r in rows:
            d = dict(r)
            d.setdefault("evaluated", False)
            out.append(d)
        return out

    return rows


@router.get("/surveys/code/{codigo}/teachers")
def listar_docentes_por_codigo(
    codigo: str,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    # 1) Obtener el id de la encuesta por código
    survey = db.execute(
        text("SELECT id FROM public.surveys WHERE codigo = :codigo"),
        {"codigo": codigo},
    ).mappings().first()
    if not survey:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")

    # 2) Listar docentes asignados
    rows = db.execute(
        text("""
            SELECT t.id, t.identificador, t.nombre, t.programa, t.estado
            FROM public.survey_teacher_assignments sta
            JOIN public.teachers t ON t.id = sta.teacher_id
            WHERE sta.survey_id = :sid
              AND (
                :q IS NULL OR
                t.nombre ILIKE '%' || :q || '%' OR
                t.identificador ILIKE '%' || :q || '%' OR
                COALESCE(t.programa, '') ILIKE '%' || :q || '%'
              )
            ORDER BY t.nombre
            LIMIT :limit OFFSET :offset
        """),
        {"sid": str(survey["id"]), "q": q, "limit": limit, "offset": offset},
    ).mappings().all()

    return rows  # [] si no hay asignaciones
