# api/app/schemas/admin.py
from __future__ import annotations
from typing import Literal, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# -------- Assign Teachers --------
class AssignTeachersIn(BaseModel):
    teacher_ids: List[UUID] = Field(default_factory=list, description="IDs de docentes")
    mode: Optional[Literal["add", "remove", "set"]] = Field(
        default="add",
        description="Estrategia: add (suma), remove (quita), set (reemplaza todo por los enviados)."
    )


class AssignTeachersOut(BaseModel):
    survey_id: UUID
    mode: Literal["add", "remove", "set"]
    before: int
    after: int
    added: int
    removed: int
    unchanged: int


# -------- Update Question Weight --------
class UpdateQuestionWeightIn(BaseModel):
    peso: float = Field(..., gt=0, description="Peso > 0; admite decimales")


class QuestionOut(BaseModel):
    id: UUID
    survey_id: UUID
    section_id: UUID
    codigo: str
    enunciado: str
    tipo: str
    orden: int
    peso: float
