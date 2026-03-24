#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings


def _mask_url(url: str) -> str:
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", url)


def _type_name(col_type) -> str:
    return str(col_type).upper()


def _looks_uuid(type_name: str) -> bool:
    return "UUID" in type_name


def _looks_int(type_name: str) -> bool:
    return any(token in type_name for token in ("INTEGER", "BIGINT", "SMALLINT"))


@dataclass
class Finding:
    level: str  # info | warn | critical
    code: str
    message: str


def _get_columns(insp, table: str) -> Dict[str, str]:
    for schema in ("public", None):
        try:
            cols = insp.get_columns(table, schema=schema)
            if cols:
                return {c["name"]: _type_name(c["type"]) for c in cols}
        except Exception:
            continue
    return {}


def _table_exists(insp, table: str) -> bool:
    try:
        return insp.has_table(table, schema="public") or insp.has_table(table)
    except Exception:
        # fallback si has_table falla por dialecto
        names = set(insp.get_table_names()) | set(insp.get_table_names(schema="public"))
        return table in names


def run_preflight(engine: Engine) -> Tuple[List[Finding], Dict[str, Dict[str, str]]]:
    insp = inspect(engine)
    findings: List[Finding] = []

    required_tables = [
        "users",
        "roles",
        "user_roles",
        "teachers",
        "surveys",
        "questions",
        "attempts",
        "responses",
        "attempt_limits",
        "audit_logs",
    ]
    optional_tables = ["turnos"]

    column_map: Dict[str, Dict[str, str]] = {}

    for t in required_tables:
        if not _table_exists(insp, t):
            findings.append(Finding("critical", f"missing_table:{t}", f"Falta tabla requerida: {t}"))
        else:
            column_map[t] = _get_columns(insp, t)

    for t in optional_tables:
        if not _table_exists(insp, t):
            findings.append(
                Finding(
                    "warn",
                    f"missing_table:{t}",
                    f"Falta tabla opcional esperada por runtime: {t}",
                )
            )
        else:
            column_map[t] = _get_columns(insp, t)

    # columnas de compatibilidad críticas para runtime actual
    required_cols = {
        "attempts": ["survey_id", "user_id", "teacher_id", "estado", "expires_at", "creado_en", "actualizado_en"],
        "responses": ["attempt_id", "question_id", "valor_likert", "texto", "created_at"],
        "attempt_limits": ["survey_id", "user_id", "extra_otorgados", "max_intentos"],
        "audit_logs": ["payload", "ip", "ua", "creado_en"],
    }
    for table, cols in required_cols.items():
        for c in cols:
            if c not in column_map.get(table, {}):
                level = "critical" if table in ("attempts", "responses", "attempt_limits") else "warn"
                findings.append(Finding(level, f"missing_column:{table}.{c}", f"Falta columna {table}.{c}"))

    # compatibilidad doble nomenclatura audit_logs (histórico)
    alog = column_map.get("audit_logs", {})
    if alog:
        if "user_id" not in alog and "actor_user_id" not in alog:
            findings.append(
                Finding(
                    "warn",
                    "audit_actor_missing",
                    "audit_logs no tiene ni user_id ni actor_user_id",
                )
            )
        if "accion" not in alog and "action" not in alog:
            findings.append(
                Finding(
                    "warn",
                    "audit_action_missing",
                    "audit_logs no tiene ni accion ni action",
                )
            )

    # chequeo de tipo PK/FK para detectar drift UUID vs INTEGER (solo advertencia)
    for table, col in [
        ("periods", "id"),
        ("surveys", "id"),
        ("surveys", "periodo_id"),
        ("survey_sections", "id"),
        ("survey_sections", "survey_id"),
        ("questions", "id"),
        ("questions", "survey_id"),
        ("questions", "section_id"),
    ]:
        if _table_exists(insp, table):
            cols = _get_columns(insp, table)
            column_map[table] = cols
            if col in cols:
                tname = cols[col]
                if not (_looks_uuid(tname) or _looks_int(tname)):
                    findings.append(
                        Finding(
                            "warn",
                            f"unexpected_type:{table}.{col}",
                            f"Tipo inesperado en {table}.{col}: {tname}",
                        )
                    )

    return findings, column_map


def main() -> int:
    db_url = settings.db_url
    print(f"[preflight] DB: {_mask_url(db_url)}")

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            # sanity check de conectividad
            conn.execute(text("SELECT 1"))

            try:
                alembic_rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
                alembic_versions = [r[0] for r in alembic_rows]
            except Exception:
                alembic_versions = []

        findings, column_map = run_preflight(engine)
        if not alembic_versions:
            findings.append(
                Finding(
                    "warn",
                    "alembic_version_missing_or_unreadable",
                    "No se pudieron leer versiones en alembic_version (tabla ausente o permisos).",
                )
            )
    except SQLAlchemyError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False, indent=2))
        return 2

    summary = {
        "ok": not any(f.level == "critical" for f in findings),
        "alembic_versions": alembic_versions,
        "findings": [asdict(f) for f in findings],
        "tables_checked": sorted(column_map.keys()),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if any(f.level == "critical" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
