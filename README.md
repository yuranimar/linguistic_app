# Gestor Lingüístico

Aplicación web MVP para gestionar operaciones de una empresa de servicios lingüísticos. Permite administrar clientes, lingüistas, proyectos de traducción e interpretación, autenticación de usuarios, y aprobación de accesos por parte de un administrador.

## Descripción

Este proyecto fue desarrollado como una solución operativa para coordinar:

- clientes que solicitan servicios lingüísticos,
- lingüistas disponibles por especialidad,
- proyectos con idioma, volumen, deadline y costo,
- usuarios del sistema con roles y estados de aprobación,
- seguimiento del flujo operativo de cada proyecto.

La aplicación combina una interfaz web en HTML con un backend Flask, usando SQLite como base de datos por defecto para facilitar desarrollo local y pruebas.

## Funcionalidades

- Registro de usuarios con estado pendiente de aprobación.
- Autenticación con Flask-Login.
- Panel administrativo para aprobar o rechazar usuarios.
- CRUD de clientes y lingüistas.
- Gestión de proyectos por servicio, idioma y estado.
- API REST para listar y actualizar proyectos.
- Panel principal del sistema con dashboard operativo.
- Scripts de inicialización y carga de datos de ejemplo.

## Stack tecnológico

- Python 3
- Flask 3.0
- Flask-SQLAlchemy
- SQLAlchemy
- Flask-Login
- SQLite
- HTML + Jinja2
- R para análisis KPI (archivo `analisis_kpi.R`)

## Estructura del proyecto

```text
linguistic_app/
├── app.py                  # Aplicación principal y factory de Flask
├── extensions.py           # Extensiones compartidas: DB y LoginManager
├── init_db.py              # Crea tablas y usuario administrador por defecto
├── seed.py                 # Carga datos ficticios para clientes, lingüistas y proyectos
├── requirements.txt        # Dependencias del proyecto
├── analisis_kpi.R          # Análisis de KPI para reportes operativos
├── reporte_operaciones.png  # Ejemplo de reporte visual
├── models/
│   └── __init__.py         # Modelos: Cliente, Linguista, Proyecto, Usuario
├── routes/
│   ├── admin.py            # Panel admin para usuarios
│   ├── auth.py             # Login / registro / logout
│   ├── clientes.py         # Endpoints y lógica de clientes
│   ├── linguistas.py       # Endpoints y lógica de lingüistas
│   ├── proyectos.py        # Endpoints de proyectos y actualización de estados
│   └── __init__.py
├── templates/
│   ├── admin_usuarios.html
│   ├── index.html
│   ├── login.html
│   └── registro.html
└── .gitignore
```

## Requisitos

- Python 3.10 o superior
- pip
- entorno virtual recomendado

## Instalación

```bash
git clone https://github.com/yuranimar/linguistic_app.git
cd linguistic_app
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Inicialización de la base de datos

```bash
python init_db.py
```

Este script crea las tablas necesarias y genera un usuario administrador por defecto.

## Carga de datos de ejemplo

```bash
python seed.py
```

Este comando inserta clientes, lingüistas y proyectos de ejemplo para probar la app sin necesidad de datos reales.

## Ejecución de la aplicación

```bash
python app.py
```

La aplicación quedará disponible en:

```text
http://localhost:5000/login
```

## Credenciales por defecto

Tras ejecutar `python init_db.py`, se crea este usuario administrador:

- Email: `admin@gestor.co`
- Contraseña: `admin123`

Importante: antes de usar la aplicación en producción, cambia la contraseña y ajusta la configuración de seguridad.

## Roles y estados

### Roles

- `coordinador`
- `linguista`
- `admin`

### Estados de usuario

- `pendiente`
- `activo`
- `inactivo`

### Estados de proyecto

- `recibido`
- `en_proceso`
- `revision`
- `entregado`
- `facturado`
- `cancelado`

## Endpoints principales

### Autenticación

- `GET /login`
- `POST /login`
- `GET /registro`
- `POST /registro`
- `GET /logout`

### Proyectos (API REST)

- `POST /api/proyectos`
- `GET /api/proyectos`
- `GET /api/proyectos/<id>`
- `PUT /api/proyectos/<id>/estado`

### Administración

- `GET /admin/usuarios`
- `POST /admin/usuarios/<id>/aprobar`
- `POST /admin/usuarios/<id>/rechazar`

## Variables de entorno

La app usa valores por defecto si no se configuran variables de entorno:

- `DATABASE_URL` (por defecto `sqlite:///linguistic_mvp.db`)
- `SECRET_KEY` (por defecto `dev-secret-cambia-en-prod`)

Ejemplo:

```bash
export DATABASE_URL="sqlite:///linguistic_mvp.db"
export SECRET_KEY="mi_clave_secreta"
python app.py
```

## Nota de desarrollo

Este repositorio representa un MVP funcional y no está pensado como una solución de producción completa. Para un despliegue real se recomienda:

- usar PostgreSQL/MySQL en lugar de SQLite,
- proteger secrets con variables de entorno o un gestor seguro,
- agregar tests automatizados,
- mejorar validaciones y permisos,
- revisar controles de seguridad y auditoría.

## Licencia

Este proyecto no incluye una licencia explícita en el repositorio. Si deseas reutilizarlo o publicarlo, revisa la política del propietario antes de distribuirlo.

## Autor

Repositorio de ejemplo / proyecto personal de `yuranimar`.
