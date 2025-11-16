# app/core/security.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Tuple, Iterable
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

# Solo para docs/Swagger; no ejecuta nada por sí mismo
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
ADMIN_ROLE_NAMES = {"Administrador", "Admin", "admin", "administrator"}


def create_access_token(subject: dict[str, Any], expires_minutes: int | None = None) -> str:
    """
    Genera un JWT con 'exp' e 'iat'.
    - 'sub' se normaliza a str.
    - 'iat' se pone como epoch seconds (int) para comparaciones.
    """
    if expires_minutes is None:
        expires_minutes = settings.JWT_EXPIRE_MINUTES

    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)

    claims = dict(subject)
    if "sub" in claims and not isinstance(claims["sub"], str):
        claims["sub"] = str(claims["sub"])

    to_encode = {
        **claims,
        "iat": int(now.timestamp()),
        "exp": exp,  # PyJWT acepta datetime tz-aware
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decodifica exigiendo 'exp' e 'iat' y verificando expiración.
    """
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "iat"], "verify_exp": True},
            leeway=5,  # pequeño margen por skew de reloj
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Devuelve el objeto User activo con sus roles cargados.
    """
    from sqlalchemy.orm import selectinload
    
    payload = decode_token(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token sin sujeto")

    # Normaliza a UUID (si tu PK es UUID)
    try:
        user_id = UUID(str(sub))
    except Exception:
        raise HTTPException(status_code=401, detail="Token con 'sub' inválido")

    user = (
        db.query(User)
        .options(selectinload(User.roles))
        .filter(User.id == user_id, User.estado == "activo")
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    
    # Asegurar que los roles están cargados haciendo una copia de los nombres
    # para evitar lazy loading fuera de la sesión
    if hasattr(user, 'roles') and user.roles:
        # Forzar la carga de roles accediendo a ellos dentro de la sesión
        _ = [r.nombre for r in user.roles]
    
    return user


def get_current_user_with_claims(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Tuple[User, dict]:
    """
    Igual que get_current_user pero retorna también los claims (para leer iat).
    """
    from sqlalchemy.orm import selectinload
    
    payload = decode_token(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token sin sujeto") 

    try:
        user_id = UUID(str(sub))
    except Exception:
        raise HTTPException(status_code=401, detail="Token con 'sub' inválido")

    user = (
        db.query(User)
        .options(selectinload(User.roles))
        .filter(User.id == user_id, User.estado == "activo")
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    
    # Asegurar que los roles están cargados
    if hasattr(user, 'roles') and user.roles:
        _ = [r.nombre for r in user.roles]
    
    return user, payload


def _roles_from_user(user: User) -> set[str]:
    names: set[str] = set()
    # si tienes relación user.roles (SQLAlchemy)
    if hasattr(user, "roles") and user.roles:
        for r in user.roles:
            n = getattr(r, "nombre", None) or getattr(r, "name", None)
            if n:
                names.add(str(n))
    return names

def _roles_from_claims(claims: dict | None) -> set[str]:
    if not claims:
        return set()
    raw = claims.get("roles") or claims.get("role") or []
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, Iterable):
        return {str(x) for x in raw}
    return set()

def user_is_admin(user: User, claims: dict | None = None) -> bool:
    names = set()
    names |= _roles_from_user(user)
    names |= _roles_from_claims(claims)
    # normaliza
    lower = {n.lower() for n in names}
    return (
        bool(ADMIN_ROLE_NAMES & names) or
        any(n in {"administrador","admin","administrator"} for n in lower)
    )

def get_admin_user(dep=Depends(get_current_user_with_claims)) -> User:
    user, claims = dep  # get_current_user_with_claims devuelve (user, claims)
    if not user_is_admin(user, claims):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    return user