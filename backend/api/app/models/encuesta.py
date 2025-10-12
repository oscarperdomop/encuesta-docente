# app/models/encuesta.py (fragmentos clave)
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Period(Base):
    __tablename__ = "periods"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)
    anyo = Column(Integer, nullable=False)
    semestre = Column(Integer, nullable=False)

class Survey(Base):
    __tablename__ = "surveys"
    id = Column(Integer, primary_key=True)
    codigo = Column(String, unique=True, nullable=False)  # << coincide con tu seed
    nombre = Column(String, nullable=False)
    periodo_id = Column(Integer, ForeignKey("periods.id"))
    estado = Column(String, default="activa")
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)

class SurveySection(Base):
    __tablename__ = "survey_sections"
    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), index=True)
    titulo = Column(String, nullable=False)
    orden = Column(Integer, nullable=False)

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), index=True)
    section_id = Column(Integer, ForeignKey("survey_sections.id"), index=True)
    codigo = Column(String, nullable=False)  # Q1..Q16
    enunciado = Column(String, nullable=False)
    orden = Column(Integer, nullable=False)
    tipo = Column(String, nullable=False)    # 'likert' | 'texto'
    peso = Column(Integer, default=1, nullable=False)
