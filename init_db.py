"""
init_db.py — Script de inicialización de la base de datos.

Ejecutar UNA SOLA VEZ (o cuando se cambien los modelos en desarrollo):
  $ python init_db.py

Crea todas las tablas y el usuario administrador por defecto.
"""

from app import create_app
from extensions import db
from models import Cliente, Linguista, Proyecto, Usuario, EstadoUsuario  # noqa: F401

app = create_app()

with app.app_context():
    db.create_all()
    print("✅  Tablas creadas: clientes, linguistas, proyectos, usuarios")

    # Crear usuario admin si no existe
    if not Usuario.query.filter_by(email="admin@gestor.co").first():
        admin = Usuario(
            nombre="Administrador",
            email="admin@gestor.co",
            rol="admin",
            estado=EstadoUsuario.ACTIVO,
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("✅  Usuario admin creado:")
        print("      Email:      admin@gestor.co")
        print("      Contraseña: admin123")
        print("      ⚠️  Cambia la contraseña antes de desplegar en producción.")
    else:
        print("ℹ️   Usuario admin ya existe, no se recreó.")

    print("\n    Base de datos inicializada correctamente.")
