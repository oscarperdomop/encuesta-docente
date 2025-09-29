from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict

class LoginIn(BaseModel):
    email: EmailStr

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeOut(BaseModel):
    # Permite construir desde objetos SQLAlchemy (Pydantic v2)
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    nombre: str | None = None
    roles: list[str] = []
