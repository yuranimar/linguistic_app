"""
routes/linguistas.py — Endpoints REST para la gestión de lingüistas.

Rutas expuestas:
  POST  /api/linguistas        → Registrar lingüista
  GET   /api/linguistas        → Listar (con filtro opcional por especialidad)
  GET   /api/linguistas/<id>   → Detalle de un lingüista
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Linguista

linguistas_bp = Blueprint("linguistas", __name__)


@linguistas_bp.post("/linguistas")
def crear_linguista():
    """Registra un nuevo lingüista/colaborador."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON requerido."}), 400

    if not data.get("nombre") or not data.get("email"):
        return jsonify({"error": "Los campos 'nombre' y 'email' son obligatorios."}), 422

    linguista = Linguista(
        nombre       = data["nombre"].strip(),
        email        = data["email"].strip().lower(),
        especialidad = data.get("especialidad", "").strip() or None,
        tarifa       = data.get("tarifa"),
    )

    try:
        db.session.add(linguista)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe un lingüista registrado con ese email."}), 409

    return jsonify({"mensaje": "Lingüista registrado.", "linguista": linguista.to_dict()}), 201


@linguistas_bp.get("/linguistas")
def listar_linguistas():
    """
    Lista lingüistas. Filtro opcional:
      ?especialidad=Legal  → solo lingüistas de esa especialidad
    """
    especialidad = request.args.get("especialidad")
    query = Linguista.query.order_by(Linguista.nombre)

    if especialidad:
        query = query.filter(Linguista.especialidad.ilike(f"%{especialidad}%"))

    linguistas = query.all()
    return jsonify({"linguistas": [l.to_dict() for l in linguistas], "total": len(linguistas)}), 200


@linguistas_bp.get("/linguistas/<int:linguista_id>")
def obtener_linguista(linguista_id: int):
    linguista = db.session.get(Linguista, linguista_id)
    if not linguista:
        return jsonify({"error": f"Lingüista id={linguista_id} no encontrado."}), 404
    return jsonify(linguista.to_dict()), 200
