"""
models/__init__.py — Modelos SQLAlchemy para la plataforma de servicios lingüísticos.

Entidades:
  · Cliente   — empresas o personas que solicitan servicios
  · Linguista — traductores / intérpretes disponibles
  · Proyecto  — trabajo asignado que relaciona ambas entidades
"""

import enum
import uuid
from datetime import datetime, timezone

from extensions import db


# ── Enum de estados logísticos del proyecto ───────────────────────────────────
class EstadoProyecto(str, enum.Enum):
    """
    Ciclo de vida de un proyecto.
    Heredar de str permite serializar el valor directamente a JSON sin
    necesidad de conversores personalizados.
    """
    RECIBIDO      = "recibido"       # Solicitud ingresada, sin asignar
    EN_PROCESO    = "en_proceso"     # Lingüista trabajando
    REVISION      = "revision"       # Control de calidad interno
    ENTREGADO     = "entregado"      # Enviado al cliente
    FACTURADO     = "facturado"      # Factura emitida
    CANCELADO     = "cancelado"      # Proyecto anulado


# ── Modelo: Cliente ─────────────────────────────────────────────────────────[...]
class Cliente(db.Model):
    """Representa a un cliente de la empresa de servicios lingüísticos."""

    __tablename__ = "clientes"

    id        = db.Column(db.Integer, primary_key=True)
    nombre    = db.Column(db.String(120), nullable=False)
    email     = db.Column(db.String(120), unique=True, nullable=False)
    telefono  = db.Column(db.String(30), nullable=True)

    # Relación inversa: un cliente puede tener muchos proyectos
    proyectos = db.relationship("Proyecto", back_populates="cliente", lazy="dynamic")

    # Timestamps de auditoría
    creado_en    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    actualizado_en = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        """Serialización segura a diccionario (sin exponer datos sensibles)."""
        return {
            "id":       self.id,
            "nombre":   self.nombre,
            "email":    self.email,
            "telefono": self.telefono,
        }

    def __repr__(self) -> str:
        return f"<Cliente id={self.id} nombre='{self.nombre}'>"


# ── Modelo: Linguista ────────────────────────────────────────────────────────…[...]
class Linguista(db.Model):
    """Representa a un lingüista (traductor o intérprete) del equipo."""

    __tablename__ = "linguistas"

    id          = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(120), nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    especialidad = db.Column(db.String(120), nullable=True)   # ej. "Legal", "Médica"
    # Tarifa en la moneda base de la empresa (COP, USD, etc.)
    tarifa      = db.Column(db.Numeric(10, 2), nullable=True)

    # Relación inversa
    proyectos   = db.relationship("Proyecto", back_populates="linguista", lazy="dynamic")

    creado_en      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    actualizado_en = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "nombre":       self.nombre,
            "email":        self.email,
            "especialidad": self.especialidad,
            "tarifa":       float(self.tarifa) if self.tarifa is not None else None,
        }

    def __repr__(self) -> str:
        return f"<Linguista id={self.id} nombre='{self.nombre}'>"


# ── Modelo: Proyecto ────────────────────────────────────────────────────────…[...]
class Proyecto(db.Model):
    """
    Núcleo operativo: representa un encargo de traducción o interpretación.

    Campos clave:
      · codigo_seguimiento  — identificador público único (UUID corto)
      · servicio            — "traducción", "interpretación", etc.
      · idioma              — par lingüístico, ej. "ES→EN"
      · volumen             — palabras (traducción) o horas (interpretación)
      · costo_total         — calculado externamente y almacenado aquí
      · deadline            — fecha límite de entrega
      · estado              — flujo logístico (EstadoProyecto)
    """

    __tablename__ = "proyectos"

    id                  = db.Column(db.Integer, primary_key=True)
    codigo_seguimiento  = db.Column(
        db.String(12),
        unique=True,
        nullable=False,
        default=lambda: uuid.uuid4().hex[:10].upper(),  # ej. "A3F9D12C1E"
    )

    # ── Claves foráneas (con índices para mejorar performance en filtros y joins) ─
    cliente_id   = db.Column(db.Integer, db.ForeignKey("clientes.id"),  nullable=False, index=True)
    linguista_id = db.Column(db.Integer, db.ForeignKey("linguistas.id"), nullable=True, index=True)

    # ── Relaciones ORM ───────────────────────────────────────────────────────…[...]
    cliente   = db.relationship("Cliente",   back_populates="proyectos")
    linguista = db.relationship("Linguista", back_populates="proyectos")

    # ── Datos del servicio ────────────────────────────────────────────────────
    servicio    = db.Column(db.String(60),  nullable=False)          # "traducción"
    idioma      = db.Column(db.String(20),  nullable=False)          # "ES→EN"
    volumen     = db.Column(db.Numeric(10, 2), nullable=True)        # palabras / horas
    costo_total = db.Column(db.Numeric(12, 2), nullable=True)
    deadline    = db.Column(db.DateTime,    nullable=True)

    # ── Estado logístico ──────────────────────────────────────────────────────
    estado = db.Column(
        db.Enum(EstadoProyecto),
        nullable=False,
        default=EstadoProyecto.RECIBIDO,
    )

    # ── Timestamps ─────────────────────────────────────────────────────────[...]
    creado_en      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    actualizado_en = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id":                 self.id,
            "codigo_seguimiento": self.codigo_seguimiento,
            "cliente":            self.cliente.to_dict() if self.cliente else None,
            "linguista":          self.linguista.to_dict() if self.linguista else None,
            "servicio":           self.servicio,
            "idioma":             self.idioma,
            "volumen":            float(self.volumen) if self.volumen is not None else None,
            "costo_total":        float(self.costo_total) if self.costo_total is not None else None,
            "deadline":           self.deadline.isoformat() if self.deadline else None,
            "estado":             self.estado.value,
            "creado_en":          self.creado_en.isoformat() if self.creado_en else None,
            "actualizado_en":     self.actualizado_en.isoformat() if self.actualizado_en else None,
        }

    def __repr__(self) -> str:
        return f"<Proyecto id={self.id} codigo='{self.codigo_seguimiento}' estado='{self.estado}'>"


# ── Modelo: Usuario ────────────────────────────────────────────────────────…[...]
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class EstadoUsuario(str, enum.Enum):
    """Ciclo de vida de un usuario en el sistema."""
    PENDIENTE  = "pendiente"   # Solicitó acceso, esperando aprobación del admin
    ACTIVO     = "activo"      # Aprobado, puede iniciar sesión
    INACTIVO   = "inactivo"    # Desactivado por el admin


class Usuario(UserMixin, db.Model):
    """
    Usuario del sistema con autenticación segura y aprobación por rol.
    UserMixin provee is_authenticated, is_active, get_id() automáticamente.
    Las contraseñas NUNCA se guardan en texto plano — solo su hash.
    """
    __tablename__ = "usuarios"

    id            = db.Column(db.Integer, primary_key=True)
    nombre        = db.Column(db.String(80),  nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rol           = db.Column(db.String(20),  nullable=False, default="coordinador")
    # Estado reemplaza al booleano "activo" — más expresivo y extensible
    estado        = db.Column(
        db.Enum(EstadoUsuario),
        nullable=False,
        default=EstadoUsuario.PENDIENTE
    )

    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Flask-Login llama a is_active para decidir si permite el login
    @property
    def is_active(self):
        return self.estado == EstadoUsuario.ACTIVO

    def es_admin(self) -> bool:
        return self.rol == "admin"

    def set_password(self, password: str):
        """Genera y guarda el hash de la contraseña."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifica si la contraseña coincide con el hash guardado."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id":       self.id,
            "nombre":   self.nombre,
            "email":    self.email,
            "rol":      self.rol,
            "estado":   self.estado.value,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} email='{self.email}' rol='{self.rol}' estado='{self.estado}'>"
