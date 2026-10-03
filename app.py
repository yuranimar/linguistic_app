from flask import Flask
from flask_login import login_required, current_user
from extensions import db, login_manager
from routes.proyectos import proyectos_bp
from routes.clientes import clientes_bp
from routes.linguistas import linguistas_bp
from routes.auth import auth_bp
from routes.admin import admin_bp


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)

    # Soporta PostgreSQL en Render y SQLite local.
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        database_url = "sqlite:///linguistic_mvp.db"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-cambia-en-prod")
    app.config["JSON_SORT_KEYS"] = False

    # Ajustes extra para producción
    if os.environ.get("FLASK_ENV") == "production" or os.environ.get("RENDER"):
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(proyectos_bp, url_prefix="/api")
    app.register_blueprint(clientes_bp, url_prefix="/api")
    app.register_blueprint(linguistas_bp, url_prefix="/api")

    @app.get("/")
    @login_required
    def dashboard():
        from models import Usuario, EstadoUsuario
        pendientes_count = 0
        if current_user.es_admin():
            pendientes_count = Usuario.query.filter_by(estado=EstadoUsuario.PENDIENTE).count()
        return render_template("index.html", pendientes_count=pendientes_count)

    @app.get("/health")
    def health():
        return {"status": "ok", "servicio": "Gestor Lingüístico API"}, 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
