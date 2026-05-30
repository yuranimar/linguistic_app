"""
seed.py — Poblar la base de datos con datos ficticios realistas.
Empresa de Servicios Lingüísticos — MVP Backend (Colombia)

Uso:
    python seed.py            # Inserta datos (falla si ya existen)
    python seed.py --reset    # Limpia toda la BD y vuelve a insertar

Requisitos previos:
    1. Haber ejecutado `python init_db.py` al menos una vez.
    2. Estar en el mismo directorio que app.py.
"""

import sys
from datetime import datetime, timezone, timedelta

from app import create_app
from extensions import db
from models import Cliente, Linguista, Proyecto, EstadoProyecto


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  DATOS FICTICIOS — contexto Colombia                                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

CLIENTES_DATA = [
    {
        # Firma de abogados en Bogotá con contratos internacionales frecuentes
        "nombre":   "Cavelier Abogados S.A.S.",
        "email":    "proyectos@cavelier-abogados.com.co",
        "telefono": "+57 601 321 0000",
    },
    {
        # Laboratorio farmacéutico con documentación técnica en varios idiomas
        "nombre":   "Laboratorios Lafrancol S.A.",
        "email":    "traduccion@lafrancol.com.co",
        "telefono": "+57 602 880 5500",
    },
    {
        # ONG internacional con sede en Medellín que trabaja con comunidades
        "nombre":   "Fundación Alianza por la Paz",
        "email":    "comunicaciones@alianzaporlapaz.org",
        "telefono": "+57 604 444 9800",
    },
]

LINGUISTAS_DATA = [
    {
        # Traductora jurídica certificada, par ES↔EN
        "nombre":       "Valentina Ríos Salcedo",
        "email":        "v.rios@linguistas.co",
        "especialidad": "Traducción Jurídica ES↔EN",
        # Tarifa por palabra en USD (estándar mercado colombiano exportación)
        "tarifa":       0.09,
    },
    {
        # Intérprete simultáneo con experiencia en ferias y congresos
        "nombre":       "Andrés Felipe Montoya",
        "email":        "af.montoya@linguistas.co",
        "especialidad": "Interpretación Simultánea ES↔EN↔FR",
        # Tarifa por hora en USD
        "tarifa":       65.00,
    },
    {
        # Traductora técnica-científica, par ES↔PT (importante para mercado LATAM)
        "nombre":       "Camila Suárez Herrera",
        "email":        "c.suarez@linguistas.co",
        "especialidad": "Traducción Técnica ES↔PT",
        "tarifa":       0.07,
    },
    {
        # Intérprete de enlace y traducción médica, comunidades indígenas
        "nombre":       "Jorge Iván Patiño Reyes",
        "email":        "ji.patino@linguistas.co",
        "especialidad": "Interpretación Médica ES↔EN",
        # Tarifa por media jornada (4 h)
        "tarifa":       120.00,
    },
]

# Las fechas se calculan dinámicamente desde el momento de ejecución del script
# para que los deadlines siempre sean coherentes con el estado del proyecto.
def _dias(n: int) -> datetime:
    """Retorna un datetime UTC = hoy + n días."""
    return datetime.now(timezone.utc) + timedelta(days=n)


def build_proyectos(clientes: list[Cliente], linguistas: list[Linguista]) -> list[dict]:
    """
    Construye la lista de proyectos usando los objetos ORM ya persistidos,
    de modo que los IDs estén disponibles como claves foráneas.
    """
    return [
        {
            # P1: Recién llegado, aún sin asignar lingüista
            # Contrato internacional de Cavelier Abogados
            "codigo_seguimiento": "CBG-2025-001",
            "cliente_id":         clientes[0].id,          # Cavelier
            "linguista_id":       None,                     # pendiente de asignación
            "servicio":           "Traducción Jurídica",
            "idioma":             "ES→EN",
            "volumen":            8_200,                    # palabras
            "costo_total":        738.00,                   # 8200 * $0.09 USD
            "deadline":           _dias(12),
            "estado":             EstadoProyecto.RECIBIDO,
        },
        {
            # P2: En proceso — Lafrancol necesita ficha técnica en portugués
            "codigo_seguimiento": "LFL-2025-047",
            "cliente_id":         clientes[1].id,           # Lafrancol
            "linguista_id":       linguistas[2].id,         # Camila (ES↔PT)
            "servicio":           "Traducción Técnica",
            "idioma":             "ES→PT",
            "volumen":            5_600,                    # palabras
            "costo_total":        392.00,                   # 5600 * $0.07 USD
            "deadline":           _dias(7),
            "estado":             EstadoProyecto.EN_PROCESO,
        },
        {
            # P3: En revisión — Interpretación simultánea para congreso de paz
            # (ya se realizó, ahora se revisa el acta y el informe del intérprete)
            "codigo_seguimiento": "FAP-2025-012",
            "cliente_id":         clientes[2].id,           # Fundación Alianza
            "linguista_id":       linguistas[1].id,         # Andrés (simultánea)
            "servicio":           "Interpretación Simultánea",
            "idioma":             "ES↔EN",
            "volumen":            8.0,                      # horas de servicio
            "costo_total":        520.00,                   # 8h * $65 USD
            "deadline":           _dias(-2),                # deadline ya pasó (entregado tarde)
            "estado":             EstadoProyecto.REVISION,
        },
        {
            # P4: Entregado — Contrato de confidencialidad para Cavelier
            "codigo_seguimiento": "CBG-2025-003",
            "cliente_id":         clientes[0].id,           # Cavelier (segundo proyecto)
            "linguista_id":       linguistas[0].id,         # Valentina (jurídica)
            "servicio":           "Traducción Jurídica",
            "idioma":             "EN→ES",
            "volumen":            2_100,                    # palabras
            "costo_total":        189.00,                   # 2100 * $0.09 USD
            "deadline":           _dias(-5),                # ya fue entregado
            "estado":             EstadoProyecto.ENTREGADO,
        },
    ]


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  LÓGICA DE SEED                                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def limpiar_bd():
    """Elimina todos los registros en orden correcto (respetando FK)."""
    Proyecto.query.delete()
    Linguista.query.delete()
    Cliente.query.delete()
    db.session.commit()
    print("  🗑️  Base de datos limpiada.\n")


def insertar_clientes() -> list[Cliente]:
    clientes = []
    for datos in CLIENTES_DATA:
        c = Cliente(**datos)
        db.session.add(c)
        clientes.append(c)

    db.session.flush()  # Obtiene los IDs sin hacer commit aún
    print(f"  ✅  {len(clientes)} clientes insertados:")
    for c in clientes:
        print(f"       → [{c.id}] {c.nombre}  |  {c.email}")
    return clientes


def insertar_linguistas() -> list[Linguista]:
    linguistas = []
    for datos in LINGUISTAS_DATA:
        l = Linguista(**datos)
        db.session.add(l)
        linguistas.append(l)

    db.session.flush()
    print(f"\n  ✅  {len(linguistas)} lingüistas insertados:")
    for l in linguistas:
        tarifa_fmt = f"USD {l.tarifa:.2f}"
        print(f"       → [{l.id}] {l.nombre}  |  {l.especialidad}  |  {tarifa_fmt}")
    return linguistas


def insertar_proyectos(clientes: list[Cliente], linguistas: list[Linguista]) -> list[Proyecto]:
    proyectos_data = build_proyectos(clientes, linguistas)
    proyectos = []
    for datos in proyectos_data:
        p = Proyecto(**datos)
        db.session.add(p)
        proyectos.append(p)

    db.session.flush()
    print(f"\n  ✅  {len(proyectos)} proyectos insertados:")
    for p in proyectos:
        linguista_nombre = p.linguista.nombre if p.linguista else "Sin asignar"
        deadline_fmt = p.deadline.strftime("%d/%m/%Y") if p.deadline else "—"
        print(
            f"       → [{p.codigo_seguimiento}]  "
            f"{p.servicio} {p.idioma}  |  "
            f"Estado: {p.estado.value.upper():<12}  |  "
            f"Lingüista: {linguista_nombre:<28}  |  "
            f"Deadline: {deadline_fmt}  |  "
            f"USD {p.costo_total:.2f}"
        )
    return proyectos


def run_seed(reset: bool = False):
    app = create_app()

    with app.app_context():
        print("\n" + "═" * 65)
        print("  🌱  SEED — Gestor Lingüístico")
        print("═" * 65 + "\n")

        if reset:
            limpiar_bd()

        # Verificar si ya hay datos para evitar duplicados accidentales
        if not reset and Cliente.query.first():
            print("  ⚠️  Ya existen datos en la base de datos.")
            print("      Usa `python seed.py --reset` para limpiar e reinsertar.\n")
            sys.exit(0)

        try:
            clientes   = insertar_clientes()
            linguistas = insertar_linguistas()
            proyectos  = insertar_proyectos(clientes, linguistas)  # noqa: F841

            db.session.commit()

            print("\n" + "─" * 65)
            print(f"  🎉  Seed completado exitosamente.")
            print(f"      Registros insertados: "
                  f"{len(clientes)} clientes · "
                  f"{len(linguistas)} lingüistas · "
                  f"{len(proyectos)} proyectos")
            print("─" * 65 + "\n")

        except Exception as exc:
            db.session.rollback()
            print(f"\n  ❌  Error durante el seed: {exc}")
            print("      Todos los cambios fueron revertidos (rollback).\n")
            raise


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PUNTO DE ENTRADA                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    run_seed(reset=reset_flag)
