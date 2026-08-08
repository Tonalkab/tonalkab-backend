# backend/app/create_admin.py
import sys
from app.db import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def crear_o_promover_admin(nombre: str, email: str, password: str = None):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.es_admin = True
            if nombre:
                user.nombre = nombre
            if password:
                user.password_hash = hash_password(password)
            db.commit()
            print(f"✅ El usuario existente '{email}' ahora es ADMINISTRADOR (es_admin = True).")
        else:
            if not password:
                print("❌ Error: Para crear un nuevo usuario debes proporcionar una contraseña.")
                return
            
            nuevo_admin = User(
                nombre=nombre or "Administrador",
                email=email,
                password_hash=hash_password(password),
                id_estado_cuenta=1,
                monedas=1000,
                es_admin=True
            )
            db.add(nuevo_admin)
            db.commit()
            print(f"✨ ¡Usuario Administrador '{email}' creado exitosamente con 1000 monedas iniciales!")
    except Exception as e:
        db.rollback()
        print(f"❌ Ocurrió un error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        nombre_arg = sys.argv[1]
        email_arg = sys.argv[2]
        password_arg = sys.argv[3] if len(sys.argv) > 3 else None
        crear_o_promover_admin(nombre_arg, email_arg, password_arg)
    else:
        print("Uso: python -m app.create_admin <Nombre> <Email> [Password]")
        print("Ejemplo creación: python -m app.create_admin \"Admin Tonalkab\" \"admin@tonalkab.com\" \"Admin1234*\"")
        print("Ejemplo promover existente: python -m app.create_admin \"\" \"mi_correo@gmail.com\"")
