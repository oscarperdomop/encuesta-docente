# api/app/api/v1/endpoints/admin_roles.py
from __future__ import annotations

from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import get_admin_user
from app.db.session import get_db
from app.models.user import User, Role, UserRole
from app.schemas.admin_roles import (
    RoleChangeIn, RoleChangeOut,
    UserRolesOut, AvailableRolesOut,
)

router = APIRouter(tags=["admin/roles"])


def _norm(s: str | None) -> str:
    return (s or "").strip()


def _get_role_by_name(db: Session, name: str) -> Role | None:
    """Búsqueda case-insensitive por nombre de rol."""
    return (
        db.query(Role)
        .filter(func.lower(Role.nombre) == func.lower(name))
        .first()
    )


def _list_roles_for_user(db: Session, user_id: UUID) -> List[str]:
    q = (
        db.query(Role.nombre)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .order_by(Role.nombre.asc())
    )
    return [r[0] for r in q.all()]


@router.get("/roles/available", response_model=AvailableRolesOut)
def get_available_roles(
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user),
):
    names = [r.nombre for r in db.query(Role).order_by(Role.nombre.asc()).all()]
    return AvailableRolesOut(roles=names)


@router.get("/roles", response_model=UserRolesOut)
def get_user_roles(
    user_id: UUID = Query(..., description="ID del usuario"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    roles = _list_roles_for_user(db, user_id)
    return UserRolesOut(user_id=user.id, email=user.email, roles=roles)


@router.post("/roles/grant", response_model=RoleChangeOut)
def grant_role(
    payload: RoleChangeIn,
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user),
):
    role_name = _norm(payload.role)
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    role = _get_role_by_name(db, role_name)
    if not role:
        raise HTTPException(status_code=404, detail=f"Rol no existe: {role_name}")

    exists = (
        db.query(UserRole)
        .filter(UserRole.user_id == user.id, UserRole.role_id == role.id)
        .first()
    )
    if exists:
        roles_after = _list_roles_for_user(db, user.id)
        return RoleChangeOut(
            user_id=user.id, role=role.nombre,
            action="granted", changed=False,
            roles_after=roles_after
        )

    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()

    roles_after = _list_roles_for_user(db, user.id)
    return RoleChangeOut(
        user_id=user.id, role=role.nombre,
        action="granted", changed=True,
        roles_after=roles_after
    )


@router.post("/roles/revoke", response_model=RoleChangeOut)
def revoke_role(
    payload: RoleChangeIn,
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user),
):
    role_name = _norm(payload.role)
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    role = _get_role_by_name(db, role_name)
    if not role:
        raise HTTPException(status_code=404, detail=f"Rol no existe: {role_name}")

    # Protección: no dejar al sistema sin administradores
    if role.nombre.lower() == "administrador":
        # ¿Cuántos admins hay?
        admin_count = (
            db.query(func.count(UserRole.user_id))
            .join(Role, Role.id == UserRole.role_id)
            .filter(func.lower(Role.nombre) == "administrador")
            .scalar()
        )
        # ¿Este usuario es admin?
        is_admin_user = (
            db.query(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .filter(UserRole.user_id == user.id, func.lower(Role.nombre) == "administrador")
            .first()
            is not None
        )
        # Si es el último admin, no se puede revocar
        if is_admin_user and admin_count <= 1:
            raise HTTPException(status_code=409, detail="No se puede remover el último administrador")

    row = (
        db.query(UserRole)
        .filter(UserRole.user_id == user.id, UserRole.role_id == role.id)
        .first()
    )
    if not row:
        roles_after = _list_roles_for_user(db, user.id)
        return RoleChangeOut(
            user_id=user.id, role=role.nombre,
            action="revoked", changed=False,
            roles_after=roles_after
        )

    db.delete(row)
    db.commit()

    roles_after = _list_roles_for_user(db, user.id)
    return RoleChangeOut(
        user_id=user.id, role=role.nombre,
        action="revoked", changed=True,
        roles_after=roles_after
    )
