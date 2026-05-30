"""
routes/admin.py — Panel de administración de usuarios.

Rutas (solo accesibles por admin):
  GET  /admin/usuarios                  → Lista usuarios por estado
  POST /admin/usuarios/<id>/aprobar     → Activa la cuenta
  POST /admin/usuarios/<id>/rechazar    → Desactiva la cuenta
"""

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Usuario, EstadoUsuario

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def solo_admin():
    if not current_user.is_authenticated or not current_user.es_admin():
        abort(403)


@admin_bp.get("/usuarios")
@login_required
def usuarios():
    solo_admin()
    pendientes = Usuario.query.filter_by(estado=EstadoUsuario.PENDIENTE).order_by(Usuario.creado_en.desc()).all()
    activos    = Usuario.query.filter_by(estado=EstadoUsuario.ACTIVO).order_by(Usuario.nombre).all()
    inactivos  = Usuario.query.filter_by(estado=EstadoUsuario.INACTIVO).order_by(Usuario.nombre).all()
    return render_template("admin_usuarios.html",
                           pendientes=pendientes, activos=activos, inactivos=inactivos)


@admin_bp.post("/usuarios/<int:usuario_id>/aprobar")
@login_required
def aprobar(usuario_id):
    solo_admin()
    u = db.session.get(Usuario, usuario_id)
    if not u:
        flash("Usuario no encontrado.", "error")
    elif u.es_admin():
        flash("No puedes modificar una cuenta de administrador.", "error")
    else:
        u.estado = EstadoUsuario.ACTIVO
        db.session.commit()
        flash(f"✓ Cuenta de {u.nombre} aprobada. Ya puede iniciar sesión.", "success")
    return redirect(url_for("admin.usuarios"))


@admin_bp.post("/usuarios/<int:usuario_id>/rechazar")
@login_required
def rechazar(usuario_id):
    solo_admin()
    u = db.session.get(Usuario, usuario_id)
    if not u:
        flash("Usuario no encontrado.", "error")
    elif u.es_admin():
        flash("No puedes modificar una cuenta de administrador.", "error")
    else:
        u.estado = EstadoUsuario.INACTIVO
        db.session.commit()
        flash(f"Cuenta de {u.nombre} desactivada.", "info")
    return redirect(url_for("admin.usuarios"))
