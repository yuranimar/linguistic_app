"""
routes/auth.py — Autenticación: login, logout y registro con aprobación.

Rutas:
  GET/POST /login     → Inicio de sesión
  GET      /logout    → Cierre de sesión
  GET/POST /registro  → Solicitud de acceso (queda en estado pendiente)
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import Usuario, EstadoUsuario

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@auth_bp.post("/login")
def login_post():
    email    = request.form.get("email",    "").strip().lower()
    password = request.form.get("password", "").strip()
    recordar = request.form.get("recordar") == "on"

    usuario = Usuario.query.filter_by(email=email).first()

    # Credenciales incorrectas
    if not usuario or not usuario.check_password(password):
        flash("Email o contraseña incorrectos.", "error")
        return render_template("login.html", email=email), 401

    # Cuenta pendiente de aprobación
    if usuario.estado == EstadoUsuario.PENDIENTE:
        flash("Tu cuenta está pendiente de aprobación. El administrador te notificará.", "warning")
        return render_template("login.html", email=email), 403

    # Cuenta desactivada
    if usuario.estado == EstadoUsuario.INACTIVO:
        flash("Tu cuenta ha sido desactivada. Contacta al administrador.", "error")
        return render_template("login.html", email=email), 403

    login_user(usuario, remember=recordar)
    flash(f"Bienvenida, {usuario.nombre}.", "success")
    next_page = request.args.get("next")
    return redirect(next_page or url_for("dashboard"))


@auth_bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.get("/registro")
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("registro.html")


@auth_bp.post("/registro")
def registro_post():
    nombre   = request.form.get("nombre",   "").strip()
    email    = request.form.get("email",    "").strip().lower()
    password = request.form.get("password", "").strip()
    confirmar= request.form.get("confirmar","").strip()
    rol      = request.form.get("rol",      "coordinador")

    # Validaciones
    if not nombre or not email or not password:
        flash("Todos los campos son obligatorios.", "error")
        return render_template("registro.html", nombre=nombre, email=email, rol=rol), 422

    if len(password) < 6:
        flash("La contraseña debe tener al menos 6 caracteres.", "error")
        return render_template("registro.html", nombre=nombre, email=email, rol=rol), 422

    if password != confirmar:
        flash("Las contraseñas no coinciden.", "error")
        return render_template("registro.html", nombre=nombre, email=email, rol=rol), 422

    if rol not in ("coordinador", "linguista"):
        flash("Rol no válido.", "error")
        return render_template("registro.html", nombre=nombre, email=email, rol=rol), 422

    if Usuario.query.filter_by(email=email).first():
        flash("Ya existe una cuenta con ese correo.", "error")
        return render_template("registro.html", nombre=nombre, email=email, rol=rol), 409

    # Crear usuario en estado PENDIENTE
    nuevo = Usuario(
        nombre = nombre,
        email  = email,
        rol    = rol,
        estado = EstadoUsuario.PENDIENTE,
    )
    nuevo.set_password(password)
    db.session.add(nuevo)
    db.session.commit()

    flash("Solicitud enviada correctamente. El administrador revisará tu acceso.", "success")
    return redirect(url_for("auth.login"))
