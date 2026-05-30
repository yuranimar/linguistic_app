"""
extensions.py — Instancias de extensiones Flask compartidas entre módulos.
Se declaran aquí para evitar importaciones circulares.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Base de datos
db = SQLAlchemy()

# Gestor de sesiones de usuario
login_manager = LoginManager()
login_manager.login_view      = "auth.login"       # redirige aquí si no hay sesión
login_manager.login_message   = "Inicia sesión para acceder al sistema."
login_manager.login_message_category = "warning"
