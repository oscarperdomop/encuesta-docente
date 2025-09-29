# api/app/schemas/admin_roles.py
from __future__ import annotations
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field


class RoleChangeIn(BaseModel):
    user_id: UUID
    role: str = Field(..., description="Nombre del rol, p.ej. 'Administrador'")


class RoleChangeOut(BaseModel):
    user_id: UUID
    role: str
    action: str  # "granted" | "revoked"
    changed: bool
    roles_after: List[str]


class UserRolesOut(BaseModel):
    user_id: UUID
    email: str
    roles: List[str]


class AvailableRolesOut(BaseModel):
    roles: List[str]
