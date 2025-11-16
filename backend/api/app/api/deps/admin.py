# api/app/api/deps/admin.py
from fastapi import Depends, HTTPException
from app.core.security import get_current_user

def require_admin(user = Depends(get_current_user)):
    """
    Acepta user como objeto o dict. Requiere 'admin' o 'superadmin' en roles.
    """
    roles = set()
    if hasattr(user, "roles"):
        roles = {getattr(r, "nombre", r) for r in (getattr(user, "roles", []) or [])}
    else:
        try:
            roles = set((user or {}).get("roles") or [])
        except Exception:
            roles = set()

    if not ({"admin", "superadmin"} & roles):
        raise HTTPException(status_code=403, detail="Solo administradores")
    return user
