# api/app/schemas/imports.py
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class RowError(BaseModel):
    row: int = Field(..., description="Número de fila (1-based, incluyendo encabezado)")
    message: str

class ImportSummary(BaseModel):
    inserted: int
    updated: int
    skipped: int


class AssignmentSummary(BaseModel):
    survey_id: UUID
    applied: bool
    requested: int
    assigned_new: int
    already_assigned: int
    total_assigned: int


class TeachersImportOut(BaseModel):
    summary: ImportSummary
    errors: List[RowError] = []
    assignment: Optional[AssignmentSummary] = None


class UsersImportSummary(BaseModel):
    inserted: int
    updated: int
    skipped: int
    roles_granted: int
    roles_existing: int


class UsersImportOut(BaseModel):
    summary: UsersImportSummary
    errors: List[RowError] = []
