from __future__ import annotations

from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core.security import get_admin_user
from app.db.session import get_db
from app.models.turno import Turno
from app.models.user import Role, User
from app.schemas.admin_users import AdminUserItem, AdminUsersListOut

router = APIRouter(tags=["admin/users"])

MAX_PER_PAGE = 50


@router.get("/usuarios", response_model=AdminUsersListOut)
def admin_list_usuarios(
    search: Optional[str] = Query(None, description="Busca por email o nombre"),
    rol: Optional[str] = Query(None, description="Filtra por nombre de rol"),
    estado: Optional[str] = Query(None, description="activo | inactivo"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=MAX_PER_PAGE),
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user),
):
    q = db.query(User).options(selectinload(User.roles))

    if search:
        term = f"%{search.strip()}%"
        q = q.filter(
            User.email.ilike(term) | User.nombre.ilike(term)
        )

    if estado:
        estado_norm = estado.strip().lower()
        if estado_norm in {"activo", "inactivo"}:
            q = q.filter(func.lower(User.estado) == estado_norm)

    if rol:
        rol_norm = rol.strip().lower()
        if rol_norm:
            q = (
                q.join(User.roles)
                .filter(func.lower(Role.nombre) == rol_norm)
                .distinct()
            )

    total = int(q.count() or 0)
    offset = (page - 1) * per_page

    users = (
        q.order_by(User.creado_en.desc().nullslast(), User.email.asc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    user_ids = [u.id for u in users]
    turnos_map = {}
    if user_ids:
        rows = (
            db.query(Turno.user_id, func.count(Turno.id))
            .filter(Turno.user_id.in_(user_ids), Turno.status == "closed")
            .group_by(Turno.user_id)
            .all()
        )
        turnos_map = {uid: int(cnt) for uid, cnt in rows}

    items = [
        AdminUserItem(
            id=u.id,
            email=u.email,
            nombre=u.nombre,
            roles=sorted([r.nombre for r in (u.roles or []) if r.nombre]),
            estado=u.estado,
            turnos_usados=turnos_map.get(u.id, 0),
            fecha_creacion=u.creado_en,
        )
        for u in users
    ]

    pages = ceil(total / per_page) if total > 0 else 1
    return AdminUsersListOut(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )

