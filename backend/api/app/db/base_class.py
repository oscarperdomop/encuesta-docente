# api/app/db/base_class.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base declarativa común para todos los modelos SQLAlchemy."""
    pass
