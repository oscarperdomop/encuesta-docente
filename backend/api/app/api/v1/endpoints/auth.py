# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import create_access_token, get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.turno import Turno
from app.schemas.auth import LoginIn, TokenOut, MeOut

router = APIRouter(prefix="/auth", tags=["auth"])

# Límite de turnos cerrados permitidos antes de bloquear el login
MAX_TURNOS = getattr(settings, "MAX_TURNOS", 2)


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    """
    Login por correo USCO. Antes de emitir el token,
    valida la cantidad de turnos CERRADOS del usuario.
    Si alcanzó el tope (MAX_TURNOS), bloquea con 403.
    """
    email = (data.email or "").strip().lower()
    if not email.endswith("@usco.edu.co"):
        raise HTTPException(status_code=401, detail="Correo no autorizado")

    user = (
        db.query(User)
        .filter(User.email == email, User.estado == "activo")
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    # Conteo de turnos CERRADOS (consumidos)
    closed_count = (
        db.query(func.count(Turno.id))
        .filter(Turno.user_id == user.id, Turno.status == "closed")
        .scalar()
    ) or 0

    if closed_count >= MAX_TURNOS:
        # Bloquea el login: no emitir token
        raise HTTPException(
            status_code=403,
            detail=(
                "Ya no tienes turnos para responder la encuesta, "
                "contacta con el administrador de la encuesta."
            ),
        )

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenOut(access_token=token)


@router.get("/me", response_model=MeOut)
def me(current_user: User = Depends(get_current_user)):
    """
    Devuelve el usuario actual según el token.
    """
    roles = [r.nombre for r in getattr(current_user, "roles", [])]
    return MeOut(
        id=current_user.id,
        email=current_user.email,
        nombre=current_user.nombre,
        roles=roles,
    )
