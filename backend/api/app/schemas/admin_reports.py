# api/app/schemas/admin_reports.py
from uuid import UUID
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict

class SectionScore(BaseModel):
    section_id: UUID
    titulo: str
    score: Optional[float] = None

class SummaryOut(BaseModel):
    enviados: int
    en_progreso: int
    pendientes: int
    completion_rate: float
    score_global: Optional[float] = None
    secciones: List[SectionScore] = Field(default_factory=list)

class QuestionRowOut(BaseModel):
    question_id: UUID
    codigo: str
    enunciado: str
    orden: int
    section: str
    n: int
    mean: Optional[float] = None
    median: Optional[float] = None
    stddev: Optional[float] = None
    min: Optional[int] = None
    max: Optional[int] = None
    c1: int
    c2: int
    c3: int
    c4: int
    c5: int

class TeacherRowOut(BaseModel):
    teacher_id: UUID
    teacher_nombre: str
    programa: Optional[str] = None
    n_respuestas: int
    promedio: Optional[float] = None
    peor_question_id: Optional[UUID] = None
    peor_codigo: Optional[str] = None
    peor_enunciado: Optional[str] = None
    peor_promedio: Optional[float] = None

class TeacherQBreakdown(BaseModel):
    question_id: UUID
    codigo: str
    enunciado: str
    section: str
    n: int
    mean: Optional[float] = None
    c1: int
    c2: int
    c3: int
    c4: int
    c5: int

class CommentRow(BaseModel):
    attempt_id: UUID
    creado_en: Optional[str] = None
    positivos: Optional[str] = None
    mejorar: Optional[str] = None
    comentarios: Optional[str] = None

class AttemptAnswerRow(BaseModel):
    attempt_id: UUID
    created_at: Optional[str] = None
    valor: int

class QuestionTeacherDetailOut(BaseModel):
    question_id: UUID
    codigo: str
    enunciado: str
    section: str
    teacher_id: UUID
    teacher_nombre: str
    n: int
    avg: Optional[float] = None
    dist: Dict[str, int] = Field(default_factory=dict)       # {"1":n1...}
    attempts: List[AttemptAnswerRow] = Field(default_factory=list)
    model_config = ConfigDict(populate_by_name=True)

# ---- detalle pregunta (global + ranking por docente) ----
class QuestionGlobalOut(BaseModel):
    n: int
    avg: Optional[float] = None
    dist: Dict[str, int] = Field(default_factory=dict)

class QuestionByTeacherRow(BaseModel):
    teacher_id: UUID
    teacher_nombre: str
    n: int
    avg: Optional[float] = None

class QuestionDetailOut(BaseModel):
    question_id: UUID
    codigo: str
    enunciado: str
    section: str
    global_: QuestionGlobalOut = Field(..., alias="global")
    by_teacher: List[QuestionByTeacherRow] = Field(default_factory=list)
    model_config = ConfigDict(populate_by_name=True)

class TeacherDetailOut(BaseModel):
    teacher_id: UUID
    teacher_nombre: str
    programa: Optional[str] = None
    n_respuestas: int
    promedio: Optional[float] = None
    preguntas: List[TeacherQBreakdown]
    comentarios: List[CommentRow]

# ---- listado de comentarios ----
class CommentListItem(BaseModel):
    attempt_id: UUID
    teacher_id: UUID
    teacher_nombre: str
    created_at: Optional[str] = None
    positivos: Optional[str] = None
    mejorar: Optional[str] = None
    comentarios: Optional[str] = None

class CommentListOut(BaseModel):
    total: int
    items: List[CommentListItem] = Field(default_factory=list)

# --- Progreso diario ---
class ProgressDay(BaseModel):
    day: str               # "YYYY-MM-DD"
    sent: int              # #attempts enviados ese día
class ProgressDailyOut(BaseModel):
    series: List[ProgressDay] = Field(default_factory=list)

class SectionSummaryRow(BaseModel):
    section_id: UUID
    titulo: str
    n_preguntas: int
    n_respuestas: int
    promedio: Optional[float] = None

    mejor_question_id: Optional[UUID] = None
    mejor_codigo: Optional[str] = None
    mejor_enunciado: Optional[str] = None
    mejor_promedio: Optional[float] = None

    peor_question_id: Optional[UUID] = None
    peor_codigo: Optional[str] = None
    peor_enunciado: Optional[str] = None
    peor_promedio: Optional[float] = None

class TopBottomQuestionRow(BaseModel):
    question_id: UUID
    codigo: str
    enunciado: str
    section: str
    n: int
    avg: Optional[float] = None

class TopBottomQuestionsOut(BaseModel):
    top: List[TopBottomQuestionRow] = Field(default_factory=list)
    bottom: List[TopBottomQuestionRow] = Field(default_factory=list)

class TeacherMatrixRow(BaseModel):
    teacher_id: UUID
    teacher_nombre: str
    programa: Optional[str] = None
    n_respuestas: int
    # Valores en el mismo orden que "columns"
    values: List[Optional[float]] = Field(default_factory=list)

class TeacherMatrixOut(BaseModel):
    # Ej. ["Q1","Q2","Q3",...], ordenadas por q.orden
    columns: List[str] = Field(default_factory=list)
    rows: List[TeacherMatrixRow] = Field(default_factory=list)


# --- catálogos para filtros del dashboard ---
class TeacherFilterItem(BaseModel):
    id: UUID
    nombre: str
    programa: Optional[str] = None

class SectionFilterItem(BaseModel):
    id: UUID
    titulo: str
    n_preguntas: int

class QuestionFilterItem(BaseModel):
    id: UUID
    codigo: str
    enunciado: str
    section: str

class DateRange(BaseModel):
    min: Optional[str] = None  # "YYYY-MM-DD"
    max: Optional[str] = None  # "YYYY-MM-DD"

class FiltersOut(BaseModel):
    programas: List[str] = Field(default_factory=list)
    teachers: List[TeacherFilterItem] = Field(default_factory=list)
    sections: List[SectionFilterItem] = Field(default_factory=list)
    questions: List[QuestionFilterItem] = Field(default_factory=list)
    date_range: DateRange = Field(default_factory=DateRange)

# --- Promedios por sección para un docente ---
class TeacherSectionScore(BaseModel):
    section_id: UUID
    titulo: str
    n_respuestas: int
    promedio: Optional[float] = None

class TeacherSectionsOut(BaseModel):
    teacher_id: UUID
    teacher_nombre: str
    sections: List[TeacherSectionScore] = Field(default_factory=list)

# --- Mapa de calor de estudiantes (attempts) para un docente ---
class StudentHeatmapRow(BaseModel):
    attempt_id: UUID
    user_email: Optional[str] = None
    created_at: Optional[str] = None
    n_respuestas: int
    promedio: Optional[float] = None
    # Valores en el mismo orden que "columns"
    values: List[Optional[float]] = Field(default_factory=list)

class StudentHeatmapOut(BaseModel):
    teacher_id: UUID
    teacher_nombre: str
    # Códigos de preguntas ordenadas
    columns: List[str] = Field(default_factory=list)
    # Cada fila es un intento (estudiante)
    rows: List[StudentHeatmapRow] = Field(default_factory=list)