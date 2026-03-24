# api/app/api/deps/admin.py
from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user_with_claims, user_is_admin

def require_admin(dep=Depends(get_current_user_with_claims)):
    """
    Requiere rol administrador usando la misma lÃ³gica central de seguridad.
    Mantiene consistencia con get_admin_user para evitar reglas divergentes.
    """
    user, claims = dep
    if not user_is_admin(user, claims):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores",
        )
    return user
