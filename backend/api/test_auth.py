"""
Script de prueba para verificar autenticación y roles.
Ejecutar desde: backend/api/
Comando: python test_auth.py
"""
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.security import create_access_token, decode_token
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from sqlalchemy.orm import selectinload

def test_auth():
    print("=" * 60)
    print("TEST DE AUTENTICACIÓN Y ROLES")
    print("=" * 60)
    
    # Crear sesión de BD
    db = SessionLocal()
    
    try:
        # 1. Buscar usuario admin
        email = "admin2@usco.edu.co"
        print(f"\n1. Buscando usuario: {email}")
        
        user = (
            db.query(User)
            .options(selectinload(User.roles))
            .filter(User.email == email, User.estado == "activo")
            .first()
        )
        
        if not user:
            print(f"❌ ERROR: Usuario {email} no encontrado o inactivo")
            return
        
        print(f"✅ Usuario encontrado: {user.id}")
        print(f"   Nombre: {user.nombre}")
        print(f"   Email: {user.email}")
        print(f"   Estado: {user.estado}")
        
        # 2. Verificar roles
        print(f"\n2. Verificando roles del usuario:")
        if hasattr(user, 'roles') and user.roles:
            roles_nombres = [r.nombre for r in user.roles]
            print(f"✅ Roles encontrados: {roles_nombres}")
        else:
            print("❌ ERROR: Usuario NO tiene roles asignados")
            print("\n   Para asignar rol admin, ejecuta en PostgreSQL:")
            print(f"""
   INSERT INTO roles (nombre) VALUES ('admin') ON CONFLICT DO NOTHING;
   INSERT INTO user_roles (user_id, role_id)
   SELECT '{user.id}', r.id FROM roles r WHERE r.nombre = 'admin'
   ON CONFLICT DO NOTHING;
            """)
            return
        
        # 3. Generar token
        print(f"\n3. Generando token JWT:")
        token = create_access_token({"sub": str(user.id), "email": user.email})
        print(f"✅ Token generado (primeros 50 chars):")
        print(f"   {token[:50]}...")
        
        # 4. Decodificar token
        print(f"\n4. Decodificando token:")
        try:
            payload = decode_token(token)
            print(f"✅ Token válido")
            print(f"   sub: {payload.get('sub')}")
            print(f"   email: {payload.get('email')}")
            print(f"   iat: {payload.get('iat')}")
            print(f"   exp: {payload.get('exp')}")
        except Exception as e:
            print(f"❌ ERROR al decodificar: {e}")
            return
        
        # 5. Simular verificación de admin
        print(f"\n5. Verificando si es admin:")
        from app.api.deps.admin import require_admin
        try:
            # No podemos llamar a require_admin directamente porque es un Depends
            # Pero podemos verificar manualmente
            roles = set()
            if hasattr(user, "roles"):
                roles = {getattr(r, "nombre", r) for r in (getattr(user, "roles", []) or [])}
            
            is_admin = bool({"admin", "superadmin"} & roles)
            if is_admin:
                print(f"✅ Usuario ES admin")
            else:
                print(f"❌ Usuario NO es admin")
                print(f"   Roles detectados: {roles}")
        except Exception as e:
            print(f"❌ ERROR en verificación: {e}")
        
        # 6. Test de configuración
        print(f"\n6. Configuración JWT:")
        print(f"   JWT_SECRET configurado: {'✅' if settings.JWT_SECRET else '❌'}")
        print(f"   JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
        print(f"   JWT_EXPIRE_MINUTES: {settings.JWT_EXPIRE_MINUTES}")
        
        print("\n" + "=" * 60)
        print("RESUMEN:")
        print("=" * 60)
        print("✅ Todo configurado correctamente")
        print("\nToken de prueba para Postman:")
        print(token)
        print("\nPrueba este token en:")
        print(f"GET http://localhost:8000/api/v1/auth/me")
        print(f"Header: Authorization: Bearer {token}")
        
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_auth()
