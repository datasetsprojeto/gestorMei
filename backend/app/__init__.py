from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from datetime import datetime
from .extensions import db, jwt, bcrypt, migrate
from .routes.health import health_bp
from .routes.auth import auth_bp
from .routes.product import product_bp
from .routes.sale import sale_bp
from .routes.employee import employee_bp


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
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Permite frontend local (arquivo estatico / localhost) consumir a API
    CORS(app, resources={r"/*": {"origins": "*"}})
    
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
        if request.path != '/health':
            app.logger.info(f"{request.method} {request.path} - {request.remote_addr}")
    
    @app.after_request
    def log_response(response):
        if request.path != '/health':
            app.logger.info(f"{request.method} {request.path} - Status: {response.status_code}")
        return response
    
    # Handlers de erro global
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Recurso não encontrado",
            "message": "O recurso solicitado não existe.",
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.path
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "error": "Método não permitido",
            "message": "O método HTTP não é suportado para este recurso.",
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.path
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Erro interno: {error}")
        return jsonify({
            "error": "Erro interno do servidor",
            "message": "Ocorreu um erro inesperado. Tente novamente mais tarde.",
            "timestamp": datetime.utcnow().isoformat()
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": "Requisição inválida",
            "message": "A requisição contém dados inválidos ou malformados.",
            "timestamp": datetime.utcnow().isoformat()
        }), 400
    
    # Rota padrão
    @app.route("/")
    def index():
        return jsonify({
            "name": "GestorMEI API",
            "version": "1.0.0",
            "description": "Sistema de gestão de vendas e estoque para MEIs",
            "timestamp": datetime.utcnow().isoformat(),
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
    from sqlalchemy import inspect, text
    from app.models.user import User

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///"):
        db_path = Path(db_uri.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    db.create_all()

    # Compatibilidade com bancos ja existentes sem migracao aplicada.
    inspector = inspect(db.engine)
    if inspector.has_table("users"):
        columns = {col["name"] for col in inspector.get_columns("users")}
        if "phone" not in columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(30)"))
            db.session.commit()
            app.logger.info("Coluna users.phone adicionada automaticamente")
        if "owner_id" not in columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN owner_id INTEGER"))
            db.session.commit()
            app.logger.info("Coluna users.owner_id adicionada automaticamente")

    if inspector.has_table("products"):
        columns = {col["name"] for col in inspector.get_columns("products")}
        if "cost" not in columns:
            db.session.execute(text("ALTER TABLE products ADD COLUMN cost NUMERIC(10,2) DEFAULT 0"))
            db.session.commit()
            app.logger.info("Coluna products.cost adicionada automaticamente")
        if "min_stock" not in columns:
            db.session.execute(text("ALTER TABLE products ADD COLUMN min_stock INTEGER DEFAULT 10"))
            db.session.commit()
            app.logger.info("Coluna products.min_stock adicionada automaticamente")
        if "max_stock" not in columns:
            db.session.execute(text("ALTER TABLE products ADD COLUMN max_stock INTEGER DEFAULT 100"))
            db.session.commit()
            app.logger.info("Coluna products.max_stock adicionada automaticamente")
        if "is_active" not in columns:
            db.session.execute(text("ALTER TABLE products ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            db.session.commit()
            app.logger.info("Coluna products.is_active adicionada automaticamente")

    if inspector.has_table("sale_items"):
        columns = {col["name"] for col in inspector.get_columns("sale_items")}
        if "unit_cost" not in columns:
            db.session.execute(text("ALTER TABLE sale_items ADD COLUMN unit_cost NUMERIC(10,2) DEFAULT 0"))
            db.session.commit()
            app.logger.info("Coluna sale_items.unit_cost adicionada automaticamente")

    if inspector.has_table("sales"):
        columns = {col["name"] for col in inspector.get_columns("sales")}
        if "employee_id" not in columns:
            db.session.execute(text("ALTER TABLE sales ADD COLUMN employee_id INTEGER"))
            db.session.commit()
            app.logger.info("Coluna sales.employee_id adicionada automaticamente")

    admin_email = "admin@gestormei.com"
    admin_password = "admin123"

    if not User.query.filter_by(email=admin_email).first():
        password_hash = bcrypt.generate_password_hash(admin_password.encode("utf-8")).decode("utf-8")
        admin_user = User(name="Administrador", email=admin_email, phone="", password_hash=password_hash)
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info("Usuario admin padrao criado para primeiro acesso")