# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user
from app.core.config import settings
from pydantic import BaseModel, EmailStr
from app.db.session import get_db
from app.models.user import User, Role
from app.schemas.auth import LoginIn, TokenOut, MeOut


router = APIRouter(tags=["auth"])

@router.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    if not email.endswith("@usco.edu.co"):
        raise HTTPException(status_code=401, detail="Correo no autorizado")
    user = db.query(User).filter(User.email == email, User.estado == "activo").first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenOut(access_token=token)

@router.get("/auth/me", response_model=MeOut)
def me(current_user: User = Depends(get_current_user)):
    roles = [r.nombre for r in getattr(current_user, "roles", [])]
    return MeOut(id=current_user.id, email=current_user.email, nombre=current_user.nombre, roles=roles)
