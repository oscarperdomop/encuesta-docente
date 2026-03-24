from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AdminUserItem(BaseModel):
    id: UUID
    email: str
    nombre: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    estado: str
    turnos_usados: int = 0
    fecha_creacion: Optional[datetime] = None


class AdminUsersListOut(BaseModel):
    items: List[AdminUserItem] = Field(default_factory=list)
    total: int
    page: int
    per_page: int
    pages: int

