# app/services/audit.py
from __future__ import annotations
from typing import Any, Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

def audit_log(
    db: Session,
    *,
    user_id: Optional[UUID],
    accion: str,
    payload: Optional[dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    ip = request.client.host if (request and request.client) else None
    ua = request.headers.get("user-agent") if request else None
    db.add(AuditLog(user_id=user_id, accion=accion, payload=payload, ip=ip, ua=ua))
    # No hacemos commit aquí: se comitea junto con la transacción del endpoint.
