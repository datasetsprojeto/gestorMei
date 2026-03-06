from flask import Flask, jsonify, request, g
from flask_cors import CORS
import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from .extensions import db, jwt, bcrypt, migrate
from .routes.health import health_bp
from .routes.auth import auth_bp
from .routes.product import product_bp
from .routes.sale import sale_bp
from .routes.employee import employee_bp

_GLOBAL_RATE_LIMIT_STATE = {}


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _client_ip(req, trust_proxy_headers=False):
    if trust_proxy_headers:
        forwarded_for = req.headers.get("X-Forwarded-For", "").strip()
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
    return req.remote_addr or "unknown"


def create_app(config_name="development"):
    """Factory function para criar a aplicação Flask"""
    
    # Importar configurações DENTRO da função
    from .config import config_by_name
    
    # Configurar logging
    app = Flask(__name__)
    
    # Carregar configurações
    config_class = config_by_name[config_name]
    
    # Instanciar a classe de configuração
    if config_name == "production":
        config_obj = config_class()
    else:
        config_obj = config_class()
    
    # Aplicar configurações ao app
    for key in dir(config_obj):
        if not key.startswith('_') and not callable(getattr(config_obj, key)):
            app.config[key] = getattr(config_obj, key)

    app.url_map.strict_slashes = False
    
    # Configurar logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    if app.config.get('LOG_JSON'):
        log_format = '{"timestamp":"%(asctime)s","logger":"%(name)s","level":"%(levelname)s","message":"%(message)s"}'

    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format=log_format
    )

    cors_origins = [origin.strip() for origin in app.config.get('CORS_ORIGINS', []) if origin.strip()]
    if not cors_origins:
        cors_origins = ["http://localhost:5501"]
    CORS(app, resources={r"/*": {"origins": cors_origins}})
    
    # Inicializar extensões
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        _initialize_database(app)
    
    # Registrar blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(sale_bp)
    app.register_blueprint(employee_bp)
    
    # Middleware para logging
    @app.before_request
    def log_request():
        request_id = request.headers.get('X-Request-ID') or str(uuid4())
        g.request_id = request_id
        client_ip = _client_ip(request, app.config.get("TRUST_PROXY_HEADERS", False))
        g.client_ip = client_ip

        if app.config.get("GLOBAL_RATE_LIMIT_ENABLED", True):
            exempt_path_prefixes = ("/health", "/")
            if request.path not in exempt_path_prefixes and not request.path.startswith("/health"):
                now = datetime.now(UTC)
                key = f"{client_ip}|{request.method}"
                bucket = _GLOBAL_RATE_LIMIT_STATE.get(key)
                max_requests = int(app.config.get("GLOBAL_RATE_LIMIT_MAX_REQUESTS", 240))
                window_seconds = int(app.config.get("GLOBAL_RATE_LIMIT_WINDOW_SECONDS", 60))
                if not bucket or now >= bucket["reset_at"]:
                    _GLOBAL_RATE_LIMIT_STATE[key] = {
                        "count": 1,
                        "reset_at": now + timedelta(seconds=window_seconds),
                    }
                else:
                    bucket["count"] += 1
                    if bucket["count"] > max_requests:
                        retry_after = max(1, int((bucket["reset_at"] - now).total_seconds()))
                        response = jsonify({
                            "error": "Muitas requisições. Tente novamente em instantes.",
                            "request_id": request_id,
                        })
                        response.status_code = 429
                        response.headers["Retry-After"] = str(retry_after)
                        return response

        if request.path != '/health':
            app.logger.info(
                f"request_id={request_id} method={request.method} path={request.path} remote={client_ip}"
            )
    
    @app.after_request
    def log_response(response):
        request_id = getattr(g, 'request_id', None)
        if request_id:
            response.headers['X-Request-ID'] = request_id

        if app.config.get('ENABLE_SECURITY_HEADERS', True):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        if request.path != '/health':
            app.logger.info(
                f"request_id={request_id} method={request.method} path={request.path} status={response.status_code}"
            )
        return response
    
    # Handlers de erro global
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Recurso não encontrado",
            "message": "O recurso solicitado não existe.",
            "timestamp": _utc_now_iso(),
            "path": request.path
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "error": "Método não permitido",
            "message": "O método HTTP não é suportado para este recurso.",
            "timestamp": _utc_now_iso(),
            "method": request.method,
            "path": request.path
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Erro interno: {error}")
        return jsonify({
            "error": "Erro interno do servidor",
            "message": "Ocorreu um erro inesperado. Tente novamente mais tarde.",
            "timestamp": _utc_now_iso()
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": "Requisição inválida",
            "message": "A requisição contém dados inválidos ou malformados.",
            "timestamp": _utc_now_iso()
        }), 400
    
    # Rota padrão
    @app.route("/")
    def index():
        return jsonify({
            "name": "GestorMEI API",
            "version": "1.0.0",
            "description": "Sistema de gestão de vendas e estoque para MEIs",
            "timestamp": _utc_now_iso(),
            "endpoints": {
                "auth": {
                    "register": "POST /auth/register",
                    "login": "POST /auth/login"
                },
                "products": {
                    "list": "GET /products",
                    "create": "POST /products",
                    "get": "GET /products/{id}",
                    "update": "PUT /products/{id}",
                    "delete": "DELETE /products/{id}"
                },
                "sales": {
                    "list": "GET /sales",
                    "create": "POST /sales",
                    "get": "GET /sales/{id}",
                    "stats": "GET /sales/stats"
                },
                "employees": {
                    "list": "GET /employees",
                    "link": "POST /employees/link",
                    "unlink": "POST /employees/unlink/{employee_id}",
                    "analytics": "GET /employees/analytics"
                },
                "health": "GET /health"
            },
            "documentation": "Consulte a documentação para mais detalhes"
        })
    
    # Shell context para facilitar debugging
    @app.shell_context_processor
    def make_shell_context():
        from app.models.user import User
        from app.models.product import Product
        from app.models.sale import Sale
        from app.models.sale_item import SaleItem
        from app.models.monthly_snapshot import MonthlySnapshot
        from app.models.audit_log import AuditLog
        
        return {
            'db': db,
            'User': User,
            'Product': Product,
            'Sale': Sale,
            'SaleItem': SaleItem,
            'MonthlySnapshot': MonthlySnapshot,
            'AuditLog': AuditLog
        }
    
    return app


def _initialize_database(app):
    """Cria estrutura minima do banco e usuario admin para primeiro acesso."""
    from pathlib import Path
    from app.models.user import User

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///"):
        db_path = Path(db_uri.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    db.create_all()

    # NOTE: schema evolution should happen through Alembic migrations.

    admin_email = "admin@gestormei.com"
    admin_password = "admin123"

    if not User.query.filter_by(email=admin_email).first():
        password_hash = bcrypt.generate_password_hash(admin_password.encode("utf-8")).decode("utf-8")
        admin_user = User(name="Administrador", email=admin_email, phone="", password_hash=password_hash)
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info("Usuario admin padrao criado para primeiro acesso")