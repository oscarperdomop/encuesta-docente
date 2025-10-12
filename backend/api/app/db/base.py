# api/app/db/base.py
from app.db.base_class import Base  # <- la Base que acabamos de crear

# Importa todos los modelos que definen tablas (no pydantic)
# Ajusta los nombres según tus archivos/clases reales:
from app.models import user  # noqa: F401
from app.models import docente  # noqa: F401
from app.models import encuesta  # noqa: F401

# Opcionalmente, si quieres exponer clases, puedes importar así:
# from app.models.user import User, Role  # noqa: F401
# from app.models.docente import Docente  # noqa: F401
# from app.models.encuesta import (Period, Survey, SurveySection, Question, Teacher,  # noqa: F401
#                                  Attempt, AttemptLimit, Response, AuditLog,
#                                  SurveyTeacherAssignment, UserRole, UserTeacherPermission)
