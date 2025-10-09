# api/app/schemas/imports.py
from typing import List, Optional
from pydantic import BaseModel, Field

class RowError(BaseModel):
    row: int = Field(..., description="Número de fila (1-based, incluyendo encabezado)")
    message: str

class ImportSummary(BaseModel):
    inserted: int
    updated: int
    skipped: int

class TeachersImportOut(BaseModel):
    summary: ImportSummary
    errors: List[RowError] = []
