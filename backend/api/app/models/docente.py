from sqlalchemy import Column, String, ForeignKey, text, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    identificador = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    programa = Column(String, nullable=True)
    estado = Column(String, default="activo")

class SurveyTeacherAssignment(Base):
    __tablename__ = "survey_teacher_assignments"
    id = Column(Integer, primary_key=True)  # puedes dejarlo Integer sin problema

    # ⬇️ IMPORTANTE: ambos como UUID para que coincidan con surveys.id y teachers.id
    survey_id = Column(UUID(as_uuid=True), ForeignKey("surveys.id"), index=True, nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id"), index=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("survey_id", "teacher_id", name="uq_survey_teacher"),
    )

    teacher = relationship("Teacher")
