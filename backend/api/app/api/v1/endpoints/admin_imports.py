# api/app/api/v1/endpoints/admin_imports.py
from __future__ import annotations
import csv, io, re
from typing import List, Tuple, Dict, Set

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import get_admin_user
from app.db.session import get_db
from app.models.docente import Teacher
from app.schemas.imports import TeachersImportOut, ImportSummary, RowError
from app.models.user import User, Role, UserRole


router = APIRouter(tags=["admin/imports"])

REQUIRED_HEADERS = {"identificador", "nombre"}
OPTIONAL_HEADERS = {"programa", "estado"}
VALID_ESTADOS = {"activo", "inactivo", ""}  # vacío -> se convierte en "activo" por defecto
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ALLOWED_ROLES = {
    "administrador": "Administrador",
    "encuestador estudiante": "Encuestador Estudiante",
    "encuestador docente": "Encuestador Docente",
    "jefe de programa": "Jefe de Programa",
}

def _norm(s: str | None) -> str:
    return (s or "").strip()
def _norm_lower(s: str | None) -> str:
    return _norm(s).lower()

@router.post("/imports/teachers", response_model=TeachersImportOut)
async def import_teachers_csv(
    file: UploadFile = File(..., description="CSV con encabezado: identificador,nombre,programa,estado"),
    dry_run: bool = Query(False, description="Si true, valida y calcula pero NO escribe en BD"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user),
):
    # 1) Leer contenido (UTF-8 con BOM soportado)
    try:
        raw = await file.read()
    finally:
        await file.close()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # fallback simple a latin-1 si fuera necesario
        text = raw.decode("latin-1")

    # 2) Parsear CSV
    reader = csv.DictReader(io.StringIO(text))
    headers = {h.strip() for h in (reader.fieldnames or [])}
    missing = REQUIRED_HEADERS - headers
    if missing:
        raise HTTPException(status_code=400, detail=f"Faltan columnas requeridas: {sorted(list(missing))}")

    # 3) Cargar filas y validar básica
    rows: List[Dict[str, str]] = []
    errors: List[RowError] = []
    seen_csv: Set[str] = set()

    for idx, row in enumerate(reader, start=2):  # fila 2 = primera de datos
        ident = _norm(row.get("identificador"))
        nombre = _norm(row.get("nombre"))
        programa = _norm(row.get("programa"))
        estado = _norm(row.get("estado")).lower()

        if not ident:
            errors.append(RowError(row=idx, message="identificador vacío"))
            continue
        if not nombre:
            errors.append(RowError(row=idx, message="nombre vacío"))
            continue
        if estado not in VALID_ESTADOS:
            errors.append(RowError(row=idx, message=f"estado inválido: {estado!r}"))
            continue
        if ident in seen_csv:
            errors.append(RowError(row=idx, message=f"identificador duplicado en CSV: {ident}"))
            continue
        seen_csv.add(ident)
        if estado == "":
            estado = "activo"

        rows.append({
            "identificador": ident,
            "nombre": nombre,
            "programa": programa or None,
            "estado": estado,
        })

    # Si todo el archivo está mal, corta
    if not rows and errors:
        return TeachersImportOut(
            summary=ImportSummary(inserted=0, updated=0, skipped=len(errors)),
            errors=errors
        )

    # 4) Prefetch existentes por identificador
    idents = [r["identificador"] for r in rows]
    existing: Dict[str, Teacher] = {
        t.identificador: t
        for t in db.query(Teacher).filter(Teacher.identificador.in_(idents)).all()
    }

    inserted = 0
    updated = 0
    skipped = len(errors)

    # 5) Inserta/Actualiza
    if dry_run:
        # Simula: no escribe, solo calcula
        for r in rows:
            if r["identificador"] in existing:
                updated += 1
            else:
                inserted += 1
        # Sin commit
        return TeachersImportOut(
            summary=ImportSummary(inserted=inserted, updated=updated, skipped=skipped),
            errors=errors
        )

    # Escritura real
    try:
        for r in rows:
            ident = r["identificador"]
            if ident in existing:
                t = existing[ident]
                t.nombre = r["nombre"]
                t.programa = r["programa"]
                t.estado = r["estado"]
                updated += 1
            else:
                db.add(Teacher(
                    identificador=ident,
                    nombre=r["nombre"],
                    programa=r["programa"],
                    estado=r["estado"],
                ))
                inserted += 1
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al escribir en BD: {e}")

    return TeachersImportOut(
        summary=ImportSummary(inserted=inserted, updated=updated, skipped=skipped),
        errors=errors
    )

def _norm_estado(v: str | None) -> str:
    v = (v or "").strip().lower()
    if v in ("", "activo", "activa"): return "activo"
    if v in ("inactivo", "inactiva"): return "inactivo"
    raise ValueError(f"estado inválido: {v}")



@router.post("/imports/users") 
async def import_users(             
    file: UploadFile = File(...),
    dry_run: bool = Query(True, description="Si true, no guarda cambios"),
    db: Session = Depends(get_db),
    current=Depends(get_admin_user),
):
    # CSV: email,nombre,rol,estado
    raw = await file.read()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw.decode("latin-1")
    reader = csv.DictReader(io.StringIO(content))

    required = {"email","nombre","rol","estado"}
    headers = { (h or "").strip().lower() for h in (reader.fieldnames or []) }
    if headers != required:
        raise HTTPException(
            status_code=400,
            detail=f"Encabezados requeridos exactos: {','.join(sorted(required))}",
        )

    roles = {r.nombre: r for r in db.query(Role).all()}
    summary = {"inserted": 0, "updated": 0, "skipped": 0}
    errors: List[Dict[str, str]] = []

    for i, row in enumerate(reader, start=2):
        email = (row.get("email") or "").strip().lower()
        nombre = (row.get("nombre") or "").strip()
        rol    = (row.get("rol") or "").strip()
        estado = (row.get("estado") or "activo").strip().lower()

        if not EMAIL_RE.match(email) or not email.endswith("@usco.edu.co"):
            errors.append({"row": i, "email": email, "error": "Email inválido o fuera de dominio"})
            summary["skipped"] += 1
            continue
        if rol not in roles:
            errors.append({"row": i, "email": email, "error": f"Rol no existe: {rol}"})
            summary["skipped"] += 1
            continue
        if estado not in ("activo","inactivo"):
            errors.append({"row": i, "email": email, "error": "Estado inválido (activo|inactivo)"})
            summary["skipped"] += 1
            continue

        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, nombre=nombre, estado=estado)
            db.add(user); db.flush()
            summary["inserted"] += 1
        else:
            user.nombre = nombre
            user.estado = estado
            summary["updated"] += 1

        # 1 rol exacto
        db.query(UserRole).filter(UserRole.user_id == user.id).delete(synchronize_session=False)
        db.add(UserRole(user_id=user.id, role_id=roles[rol].id))

    if dry_run:
        db.rollback()
    else:
        db.commit()

    return {"summary": summary, "errors": errors}
