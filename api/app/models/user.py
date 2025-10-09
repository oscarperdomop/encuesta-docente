# api/app/models/user.py
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

# roles (id serial PK, nombre unique)
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)

    users = relationship("User", secondary="user_roles", back_populates="roles")


# users (id uuid PK, email unique domain en DB -> mapear a String)
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    email = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=True)
    estado = Column(String, nullable=False, server_default=text("'activo'::character varying"))
    creado_en = Column(DateTime(timezone=True), server_default=text("now()"))

    roles = relationship("Role", secondary="user_roles", back_populates="users")


# tabla puente user_roles (PK compuesta)
class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
