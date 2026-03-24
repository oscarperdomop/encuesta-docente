from __future__ import annotations

import csv
import io
import re
from typing import Dict, List, Optional, Set
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.security import get_admin_user
from app.db.session import get_db
from app.models.docente import Teacher
from app.models.user import Role, User, UserRole
from app.schemas.imports import (
    AssignmentSummary,
    ImportSummary,
    RowError,
    TeachersImportOut,
    UsersImportOut,
    UsersImportSummary,
)

router = APIRouter(tags=["admin/imports"])

REQUIRED_TEACHER_HEADERS = {"identificador", "nombre"}
REQUIRED_USER_HEADERS = {"email", "rol"}
VALID_ESTADOS = {"activo", "inactivo", ""}  # vacio -> "activo"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _norm(s: str | None) -> str:
    return (s or "").strip()


def _decode_csv(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def _build_csv_reader(content: str) -> csv.DictReader:
    """
    Crea DictReader robusto para CSV con delimitador ',' o ';'
    y soporta encabezado especial de Excel: 'sep=;'.
    """
    lines = content.splitlines()
    if lines and lines[0].strip().lower().startswith("sep="):
        delim = lines[0].split("=", 1)[1].strip() or ","
        content = "\n".join(lines[1:])
        return csv.DictReader(io.StringIO(content), delimiter=delim)

    # Heurística simple: usa ';' si hay más ';' que ',' en la primera línea.
    header = lines[0] if lines else ""
    delim = ";" if header.count(";") > header.count(",") else ","
    return csv.DictReader(io.StringIO(content), delimiter=delim)


def _ensure_active_survey(db: Session, survey_id: UUID) -> None:
    row = db.execute(
        text(
            """
            SELECT id, estado
            FROM public.surveys
            WHERE id = :sid
            """
        ),
        {"sid": str(survey_id)},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    if (row.get("estado") or "").lower() != "activa":
        raise HTTPException(status_code=409, detail="La encuesta no esta activa")


def _survey_assignments_total(db: Session, survey_id: UUID) -> int:
    return int(
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


@router.get("/imports/teachers/template.csv")
def download_teachers_template(
    current_admin=Depends(get_admin_user),
):
    """
    Descarga una plantilla CSV base para carga masiva de docentes.
    Columnas admitidas por el importador:
    identificador,nombre,programa,estado
    """
    out = io.StringIO(newline="")
    out.write("\ufeff")
    out.write("sep=;\n")  # Fuerza delimitador en Excel (locale ES)
    w = csv.writer(out, delimiter=";", lineterminator="\n")
    w.writerow(["identificador", "nombre", "programa", "estado"])
    w.writerow(["DOC-001", "Nombre Apellido", "Programa Academico", "activo"])
    out.seek(0)

    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="plantilla_docentes.csv"'},
    )


@router.post("/imports/teachers", response_model=TeachersImportOut)
async def import_teachers_csv(
    file: UploadFile = File(..., description="CSV con encabezado: identificador,nombre,programa,estado"),
    dry_run: bool = Query(False, description="Si true, valida y calcula pero NO escribe en BD"),
    survey_id: Optional[UUID] = Query(
        None,
        description="Si se envia, asigna automaticamente los docentes importados a esta encuesta activa",
    ),
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user),
):
    if survey_id is not None:
        _ensure_active_survey(db, survey_id)

    # 1) Leer contenido (UTF-8 con BOM soportado)
    try:
        raw = await file.read()
    finally:
        await file.close()
    content = _decode_csv(raw)

    # 2) Parsear CSV
    reader = _build_csv_reader(content)
    headers = {h.strip() for h in (reader.fieldnames or [])}
    missing = REQUIRED_TEACHER_HEADERS - headers
    if missing:
        raise HTTPException(status_code=400, detail=f"Faltan columnas requeridas: {sorted(list(missing))}")

    # 3) Validar filas
    rows: List[Dict[str, str | None]] = []
    errors: List[RowError] = []
    seen_csv: Set[str] = set()

    for idx, row in enumerate(reader, start=2):
        ident = _norm(row.get("identificador"))
        nombre = _norm(row.get("nombre"))
        programa = _norm(row.get("programa")) or None
        estado = _norm(row.get("estado")).lower()

        if not ident:
            errors.append(RowError(row=idx, message="identificador vacio"))
            continue
        if not nombre:
            errors.append(RowError(row=idx, message="nombre vacio"))
            continue
        if estado not in VALID_ESTADOS:
            errors.append(RowError(row=idx, message=f"estado invalido: {estado!r}"))
            continue
        if ident in seen_csv:
            errors.append(RowError(row=idx, message=f"identificador duplicado en CSV: {ident}"))
            continue
        seen_csv.add(ident)
        if estado == "":
            estado = "activo"

        rows.append(
            {
                "identificador": ident,
                "nombre": nombre,
                "programa": programa,
                "estado": estado,
            }
        )

    if not rows and errors:
        assignment = None
        if survey_id is not None:
            assignment = AssignmentSummary(
                survey_id=survey_id,
                applied=False,
                requested=0,
                assigned_new=0,
                already_assigned=0,
                total_assigned=_survey_assignments_total(db, survey_id),
            )
        return TeachersImportOut(
            summary=ImportSummary(inserted=0, updated=0, skipped=len(errors)),
            errors=errors,
            assignment=assignment,
        )

    # 4) Prefetch existentes por identificador
    idents = [str(r["identificador"]) for r in rows]
    existing: Dict[str, Teacher] = {
        t.identificador: t
        for t in db.query(Teacher).filter(Teacher.identificador.in_(idents)).all()
    }

    inserted = 0
    updated = 0
    skipped = len(errors)

    if dry_run:
        for r in rows:
            ident = str(r["identificador"])
            if ident in existing:
                updated += 1
            else:
                inserted += 1

        assignment = None
        if survey_id is not None:
            assignment = AssignmentSummary(
                survey_id=survey_id,
                applied=False,
                requested=len(rows),
                assigned_new=0,
                already_assigned=0,
                total_assigned=_survey_assignments_total(db, survey_id),
            )

        return TeachersImportOut(
            summary=ImportSummary(inserted=inserted, updated=updated, skipped=skipped),
            errors=errors,
            assignment=assignment,
        )

    # 5) Escritura real de docentes
    try:
        for r in rows:
            ident = str(r["identificador"])
            if ident in existing:
                t = existing[ident]
                t.nombre = str(r["nombre"])
                t.programa = r["programa"]
                t.estado = str(r["estado"])
                updated += 1
            else:
                db.add(
                    Teacher(
                        identificador=ident,
                        nombre=str(r["nombre"]),
                        programa=r["programa"],
                        estado=str(r["estado"]),
                    )
                )
                inserted += 1
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al escribir docentes en BD: {e}")

    # 6) Asignacion opcional a encuesta activa
    assignment = None
    if survey_id is not None:
        try:
            imported_teachers = db.query(Teacher.id).filter(Teacher.identificador.in_(idents)).all()
            imported_ids = {tid for (tid,) in imported_teachers}

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
            current_ids = {row[0] for row in current_rows}
            to_add = imported_ids - current_ids

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

            db.commit()

            assignment = AssignmentSummary(
                survey_id=survey_id,
                applied=True,
                requested=len(imported_ids),
                assigned_new=len(to_add),
                already_assigned=len(imported_ids & current_ids),
                total_assigned=_survey_assignments_total(db, survey_id),
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Docentes importados, pero fallo asignacion: {e}")

    return TeachersImportOut(
        summary=ImportSummary(inserted=inserted, updated=updated, skipped=skipped),
        errors=errors,
        assignment=assignment,
    )


@router.get("/imports/users/template.csv")
def download_users_template(
    current_admin=Depends(get_admin_user),
):
    """
    Descarga plantilla CSV para carga masiva de usuarios.
    Columnas:
    email,nombre,rol,estado
    """
    out = io.StringIO(newline="")
    out.write("\ufeff")
    out.write("sep=;\n")
    w = csv.writer(out, delimiter=";", lineterminator="\n")
    w.writerow(["email", "nombre", "rol", "estado"])
    w.writerow(["docente.observador@usco.edu.co", "Docente Observador", "Observador Docente", "activo"])
    out.seek(0)

    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="plantilla_usuarios.csv"'},
    )


@router.post("/imports/users", response_model=UsersImportOut)
async def import_users(
    file: UploadFile = File(..., description="CSV con encabezado: email,nombre,rol,estado"),
    dry_run: bool = Query(False, description="Si true, valida y calcula pero NO escribe en BD"),
    replace_roles: bool = Query(
        False,
        description="Si true, reemplaza roles del usuario por el rol del CSV. Si false, agrega el rol si falta.",
    ),
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user),
):
    # 1) Leer CSV
    try:
        raw = await file.read()
    finally:
        await file.close()
    content = _decode_csv(raw)
    reader = _build_csv_reader(content)

    headers = {(h or "").strip().lower() for h in (reader.fieldnames or [])}
    missing = REQUIRED_USER_HEADERS - headers
    if missing:
        raise HTTPException(status_code=400, detail=f"Faltan columnas requeridas: {sorted(list(missing))}")

    roles_by_lower = {(r.nombre or "").strip().lower(): r for r in db.query(Role).all()}
    if not roles_by_lower:
        raise HTTPException(status_code=409, detail="No hay roles configurados en el sistema")

    # 2) Validar filas
    rows: List[Dict[str, str | int]] = []
    errors: List[RowError] = []
    seen_csv_emails: Set[str] = set()

    for idx, row in enumerate(reader, start=2):
        email = _norm(row.get("email")).lower()
        nombre = _norm(row.get("nombre")) or None
        rol_raw = _norm(row.get("rol"))
        estado = _norm(row.get("estado")).lower()

        if not email:
            errors.append(RowError(row=idx, message="email vacio"))
            continue
        if not EMAIL_RE.match(email):
            errors.append(RowError(row=idx, message=f"email invalido: {email}"))
            continue
        if email in seen_csv_emails:
            errors.append(RowError(row=idx, message=f"email duplicado en CSV: {email}"))
            continue
        seen_csv_emails.add(email)

        if not rol_raw:
            errors.append(RowError(row=idx, message=f"rol vacio para {email}"))
            continue
        role = roles_by_lower.get(rol_raw.lower())
        if not role:
            valid_roles = sorted({r.nombre for r in roles_by_lower.values() if r.nombre})
            errors.append(RowError(row=idx, message=f"rol no existe: {rol_raw}. Roles validos: {valid_roles}"))
            continue

        if estado == "":
            estado = "activo"
        if estado not in VALID_ESTADOS:
            errors.append(RowError(row=idx, message=f"estado invalido para {email}: {estado!r}"))
            continue

        rows.append(
            {
                "email": email,
                "nombre": nombre or "",
                "estado": estado,
                "role_id": int(role.id),
            }
        )

    if not rows and errors:
        return UsersImportOut(
            summary=UsersImportSummary(
                inserted=0,
                updated=0,
                skipped=len(errors),
                roles_granted=0,
                roles_existing=0,
            ),
            errors=errors,
        )

    # 3) Prefetch usuarios existentes
    emails = [str(r["email"]) for r in rows]
    existing_users = (
        db.query(User)
        .filter(func.lower(User.email).in_(emails))
        .all()
    )
    users_by_email = {(u.email or "").lower(): u for u in existing_users}

    inserted = 0
    updated = 0
    skipped = len(errors)
    roles_granted = 0
    roles_existing = 0

    # 4) Simulacion o escritura
    try:
        for r in rows:
            email = str(r["email"])
            role_id = int(r["role_id"])
            nombre = _norm(str(r["nombre"])) or None
            estado = str(r["estado"])

            user = users_by_email.get(email)
            if not user:
                user = User(email=email, nombre=nombre, estado=estado)
                db.add(user)
                db.flush()  # obtener user.id para user_roles
                users_by_email[email] = user
                inserted += 1
            else:
                user.nombre = nombre
                user.estado = estado
                updated += 1

            if replace_roles:
                db.query(UserRole).filter(UserRole.user_id == user.id).delete(synchronize_session=False)
                db.add(UserRole(user_id=user.id, role_id=role_id))
                roles_granted += 1
                continue

            has_role = (
                db.query(UserRole)
                .filter(UserRole.user_id == user.id, UserRole.role_id == role_id)
                .first()
            )
            if has_role:
                roles_existing += 1
            else:
                db.add(UserRole(user_id=user.id, role_id=role_id))
                roles_granted += 1

        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en importacion de usuarios: {e}")

    return UsersImportOut(
        summary=UsersImportSummary(
            inserted=inserted,
            updated=updated,
            skipped=skipped,
            roles_granted=roles_granted,
            roles_existing=roles_existing,
        ),
        errors=errors,
    )
