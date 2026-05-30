"""
routes/proyectos.py — Endpoints REST para la gestión de proyectos.

Rutas expuestas:
  POST   /api/proyectos              → Crear nuevo proyecto
  GET    /api/proyectos              → Listar proyectos activos (con filtros opcionales)
  GET    /api/proyectos/<id>         → Obtener detalle de un proyecto
  PUT    /api/proyectos/<id>/estado  → Actualizar estado logístico
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Proyecto, Cliente, Linguista, EstadoProyecto

# Blueprint con nombre descriptivo; el prefijo /api se añade en create_app()
proyectos_bp = Blueprint("proyectos", __name__)

# Estados que se consideran "activos" para el filtro por defecto
ESTADOS_ACTIVOS = {
    EstadoProyecto.RECIBIDO,
    EstadoProyecto.EN_PROCESO,
    EstadoProyecto.REVISION,
}


# ── POST /api/proyectos ───────────────────────────────────────────────────────
@proyectos_bp.post("/proyectos")
def crear_proyecto():
    """
    Crea un nuevo proyecto.

    Body JSON esperado:
    {
      "cliente_id":    1,
      "linguista_id":  2,          ← opcional en el momento de creación
      "servicio":      "traducción",
      "idioma":        "ES→EN",
      "volumen":       5000,        ← palabras o horas
      "costo_total":   250.00,      ← opcional; puede calcularse después
      "deadline":      "2025-08-30T18:00:00"  ← ISO 8601, opcional
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "El cuerpo de la petición debe ser JSON válido."}), 400

    # ── Validación de campos obligatorios ─────────────────────────────────────
    campos_requeridos = ["cliente_id", "servicio", "idioma"]
    faltantes = [c for c in campos_requeridos if not data.get(c)]
    if faltantes:
        return jsonify({"error": f"Campos requeridos faltantes: {', '.join(faltantes)}"}), 422

    # ── Verificar existencia del cliente ──────────────────────────────────────
    cliente = db.session.get(Cliente, data["cliente_id"])
    if not cliente:
        return jsonify({"error": f"Cliente con id={data['cliente_id']} no encontrado."}), 404

    # ── Verificar lingüista si se proporciona ─────────────────────────────────
    linguista_id = data.get("linguista_id")
    if linguista_id:
        linguista = db.session.get(Linguista, linguista_id)
        if not linguista:
            return jsonify({"error": f"Lingüista con id={linguista_id} no encontrado."}), 404

    # ── Parseo de deadline ────────────────────────────────────────────────────
    deadline = None
    if data.get("deadline"):
        try:
            deadline = datetime.fromisoformat(data["deadline"])
        except ValueError:
            return jsonify({"error": "Formato de deadline inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS)."}), 422

    # ── Creación del proyecto ─────────────────────────────────────────────────
    nuevo_proyecto = Proyecto(
        cliente_id   = data["cliente_id"],
        linguista_id = linguista_id,
        servicio     = data["servicio"].strip(),
        idioma       = data["idioma"].strip(),
        volumen      = data.get("volumen"),
        costo_total  = data.get("costo_total"),
        deadline     = deadline,
        estado       = EstadoProyecto.RECIBIDO,  # estado inicial siempre fijo
    )

    try:
        db.session.add(nuevo_proyecto)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Error de integridad al guardar el proyecto."}), 500

    return jsonify({
        "mensaje":  "Proyecto creado exitosamente.",
        "proyecto": nuevo_proyecto.to_dict(),
    }), 201


# ── GET /api/proyectos ────────────────────────────────────────────────────────
@proyectos_bp.get("/proyectos")
def listar_proyectos():
    """
    Lista proyectos con filtros opcionales por query string:
      ?estado=en_proceso          → filtrar por estado exacto
      ?todos=true                 → incluir entregados, facturados y cancelados
      ?cliente_id=3               → filtrar por cliente
      ?linguista_id=5             → filtrar por lingüista
      ?page=1&por_pagina=20       → paginación (defecto: página 1, 20 items)
    """
    # ── Parámetros de filtro ──────────────────────────────────────────────────
    mostrar_todos = request.args.get("todos", "false").lower() == "true"
    estado_param  = request.args.get("estado")
    cliente_id    = request.args.get("cliente_id", type=int)
    linguista_id  = request.args.get("linguista_id", type=int)

    # ── Paginación ────────────────────────────────────────────────────────────
    page       = request.args.get("page", 1, type=int)
    por_pagina = request.args.get("por_pagina", 20, type=int)
    por_pagina = min(por_pagina, 100)  # límite máximo para evitar consultas masivas

    # ── Construcción de la query ──────────────────────────────────────────────
    query = Proyecto.query.order_by(Proyecto.creado_en.desc())

    if estado_param:
        try:
            estado_enum = EstadoProyecto(estado_param)
            query = query.filter(Proyecto.estado == estado_enum)
        except ValueError:
            valores_validos = [e.value for e in EstadoProyecto]
            return jsonify({
                "error": f"Estado '{estado_param}' no válido. Valores permitidos: {valores_validos}"
            }), 422
    elif not mostrar_todos:
        # Por defecto solo se devuelven proyectos "en curso"
        query = query.filter(Proyecto.estado.in_(ESTADOS_ACTIVOS))

    if cliente_id:
        query = query.filter(Proyecto.cliente_id == cliente_id)
    if linguista_id:
        query = query.filter(Proyecto.linguista_id == linguista_id)

    # ── Paginación con SQLAlchemy ─────────────────────────────────────────────
    paginacion = query.paginate(page=page, per_page=por_pagina, error_out=False)

    return jsonify({
        "proyectos":   [p.to_dict() for p in paginacion.items],
        "total":       paginacion.total,
        "pagina":      paginacion.page,
        "por_pagina":  paginacion.per_page,
        "paginas":     paginacion.pages,
    }), 200


# ── GET /api/proyectos/<id> ───────────────────────────────────────────────────
@proyectos_bp.get("/proyectos/<int:proyecto_id>")
def obtener_proyecto(proyecto_id: int):
    """Devuelve el detalle completo de un proyecto por su ID interno."""
    proyecto = db.session.get(Proyecto, proyecto_id)
    if not proyecto:
        return jsonify({"error": f"Proyecto con id={proyecto_id} no encontrado."}), 404
    return jsonify(proyecto.to_dict()), 200


# ── PUT /api/proyectos/<id>/estado ────────────────────────────────────────────
@proyectos_bp.put("/proyectos/<int:proyecto_id>/estado")
def actualizar_estado(proyecto_id: int):
    """
    Actualiza el estado logístico de un proyecto.

    Body JSON esperado:
    {
      "estado": "en_proceso"
    }

    Transiciones válidas (regla de negocio básica):
      recibido → en_proceso → revision → entregado → facturado
      cualquier estado → cancelado
    """
    data = request.get_json(silent=True)
    if not data or "estado" not in data:
        return jsonify({"error": "Se requiere el campo 'estado' en el body JSON."}), 400

    proyecto = db.session.get(Proyecto, proyecto_id)
    if not proyecto:
        return jsonify({"error": f"Proyecto con id={proyecto_id} no encontrado."}), 404

    # ── Validar que el nuevo estado exista en el enum ─────────────────────────
    try:
        nuevo_estado = EstadoProyecto(data["estado"])
    except ValueError:
        valores_validos = [e.value for e in EstadoProyecto]
        return jsonify({
            "error": f"Estado '{data['estado']}' no válido. Valores permitidos: {valores_validos}"
        }), 422

    # ── Regla de negocio: no regresar un proyecto ya cancelado ────────────────
    if proyecto.estado == EstadoProyecto.CANCELADO and nuevo_estado != EstadoProyecto.CANCELADO:
        return jsonify({
            "error": "Un proyecto cancelado no puede cambiar de estado. Cree uno nuevo si es necesario."
        }), 409

    estado_anterior   = proyecto.estado.value
    proyecto.estado   = nuevo_estado

    db.session.commit()

    return jsonify({
        "mensaje":          "Estado actualizado correctamente.",
        "id":               proyecto.id,
        "codigo_seguimiento": proyecto.codigo_seguimiento,
        "estado_anterior":  estado_anterior,
        "estado_nuevo":     nuevo_estado.value,
        "actualizado_en":   proyecto.actualizado_en.isoformat() if proyecto.actualizado_en else None,
    }), 200
