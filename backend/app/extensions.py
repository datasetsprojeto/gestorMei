from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
migrate = Migrate()

# Configuração adicional do JWT
@jwt.user_identity_loader
def user_identity_lookup(user_id):
    """Como o ID do usuário é armazenado no token"""
    return user_id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Carregar usuário a partir do token"""
    from app.models.user import User
    identity = jwt_data["sub"]
    try:
        identity = int(identity)
    except (TypeError, ValueError):
        return None
    return User.query.get(identity)

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    """Token expirado"""
    return {
        "error": "Token expirado",
        "message": "O token de acesso expirou. Faça login novamente."
    }, 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Token inválido"""
    return {
        "error": "Token inválido",
        "message": "Token de acesso inválido."
    }, 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    """Token não fornecido"""
    return {
        "error": "Token não fornecido",
        "message": "Token de acesso é necessário para acessar este recurso."
    }, 401