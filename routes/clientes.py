"""
routes/clientes.py — Endpoints REST para la gestión de clientes.

Rutas expuestas:
  POST  /api/clientes        → Crear cliente
  GET   /api/clientes        → Listar todos los clientes
  GET   /api/clientes/<id>   → Detalle de un cliente
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Cliente

clientes_bp = Blueprint("clientes", __name__)


@clientes_bp.post("/clientes")
def crear_cliente():
    """Registra un nuevo cliente en el sistema."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON requerido."}), 400

    if not data.get("nombre") or not data.get("email"):
        return jsonify({"error": "Los campos 'nombre' y 'email' son obligatorios."}), 422

    cliente = Cliente(
        nombre   = data["nombre"].strip(),
        email    = data["email"].strip().lower(),
        telefono = data.get("telefono", "").strip() or None,
    )

    try:
        db.session.add(cliente)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe un cliente registrado con ese email."}), 409

    return jsonify({"mensaje": "Cliente creado.", "cliente": cliente.to_dict()}), 201


@clientes_bp.get("/clientes")
def listar_clientes():
    """Devuelve todos los clientes ordenados por nombre."""
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    return jsonify({"clientes": [c.to_dict() for c in clientes], "total": len(clientes)}), 200


@clientes_bp.get("/clientes/<int:cliente_id>")
def obtener_cliente(cliente_id: int):
    cliente = db.session.get(Cliente, cliente_id)
    if not cliente:
        return jsonify({"error": f"Cliente id={cliente_id} no encontrado."}), 404
    return jsonify(cliente.to_dict()), 200
