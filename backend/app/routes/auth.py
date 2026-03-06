from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token
from app.extensions import db, bcrypt
from app.models.user import User
from app.services.email_service import send_password_email, EmailServiceError
import re
import logging
import secrets
import string

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Configurar logger específico para auth
logger = logging.getLogger(__name__)

# Validação de email
def is_valid_email(email):
    """Valida formato de email"""
    if not email or not isinstance(email, str):
        return False
    
    # Padrão simplificado de validação de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None


def normalize_phone(phone):
    """Normaliza telefone mantendo apenas digitos e + no inicio."""
    if not phone or not isinstance(phone, str):
        return ""
    raw = phone.strip()
    if raw.startswith("+"):
        return "+" + re.sub(r"\D", "", raw)
    return re.sub(r"\D", "", raw)


def is_valid_phone(phone):
    """Valida telefone em formato nacional/internacional simplificado."""
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return 10 <= len(digits) <= 15


def generate_temporary_password(length=12):
    """Gera senha temporaria com letras, numeros e simbolos seguros."""
    alphabet = string.ascii_letters + string.digits + "@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ======================
# REGISTRO
# ======================
@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        # Verificar se há dados JSON
        if not request.is_json:
            return jsonify({"error": "Content-Type deve ser application/json"}), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")

        # Validações básicas
        if not name or not email or not phone:
            return jsonify({"error": "Nome, e-mail e telefone sao obrigatorios"}), 400
        
        # Limpar e validar nome
        name = str(name).strip()
        if len(name) < 2:
            return jsonify({"error": "Nome deve ter pelo menos 2 caracteres"}), 400
        
        # Limpar e validar email
        email = str(email).strip().lower()
        if not is_valid_email(email):
            return jsonify({"error": "Email invalido"}), 400

        # Limpar e validar telefone
        phone = normalize_phone(str(phone))
        if not is_valid_phone(phone):
            return jsonify({"error": "Telefone invalido"}), 400

        # Verificar se email já existe
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "Email já cadastrado"}), 409

        # Gerar senha temporaria e enviar e-mail antes de persistir usuario
        password_str = generate_temporary_password()
        try:
            send_password_email(
                current_app.config,
                to_email=email,
                user_name=name,
                generated_password=password_str,
            )
        except EmailServiceError as e:
            logger.error(f"Falha de envio de e-mail no registro: {str(e)}")
            return jsonify({"error": "Nao foi possivel enviar a senha por e-mail. Verifique SMTP."}), 500

        # Criar hash da senha - garantir UTF-8
        try:
            password_bytes = password_str.encode('utf-8')
            password_hash = bcrypt.generate_password_hash(password_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao gerar hash da senha: {str(e)}")
            return jsonify({"error": "Erro ao processar senha"}), 400

        # Criar usuário
        user = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=password_hash
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({
            "message": "Conta criada com sucesso. A senha foi enviada para o e-mail informado.",
            "user": user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro no registro: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro ao registrar usuário"}), 500


# ======================
# LOGIN - VERSÃO SIMPLIFICADA E CORRIGIDA
# ======================
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        # Verificar se há dados JSON
        if not request.is_json:
            return jsonify({"error": "Content-Type deve ser application/json"}), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400

        email = data.get("email")
        password = data.get("password")

        # Validações básicas
        if not email or not password:
            return jsonify({"error": "Email e senha são obrigatórios"}), 400
        
        # Limpar email
        email = str(email).strip().lower()
        
        # Validar formato do email
        if not is_valid_email(email):
            # Retorna 400 em vez de 401 para formato inválido
            return jsonify({"error": "Email inválido"}), 400
        
        # Buscar usuário
        user = User.query.filter_by(email=email).first()

        # Mensagem genérica para segurança
        error_msg = "Credenciais inválidas"
        
        if not user:
            logger.warning(f"Tentativa de login com email não cadastrado: {email}")
            return jsonify({"error": error_msg}), 401
        
        # CORREÇÃO CRÍTICA: Verificar senha com tratamento de encoding
        try:
            # Converter senha para bytes
            password_bytes = str(password).encode('utf-8')
            
            # Verificar hash - bcrypt.check_password_hash aceita bytes ou string
            # Se o hash no banco tem problemas de encoding, vamos tentar ambos
            user_hash = user.password_hash
            
            # Tentativa 1: Hash como string (normal)
            is_valid = bcrypt.check_password_hash(user_hash, password_bytes)
            
            if not is_valid:
                # Tentativa 2: Se falhou, talvez o hash tenha problemas
                logger.warning(f"Verificação de senha falhou para {email}, tentando tratamento alternativo")
                
                # Tentar verificar com hash como bytes
                try:
                    user_hash_bytes = user_hash.encode('utf-8') if isinstance(user_hash, str) else user_hash
                    is_valid = bcrypt.check_password_hash(user_hash_bytes, password_bytes)
                except:
                    is_valid = False
            
        except Exception as e:
            logger.error(f"Erro ao verificar senha para {email}: {str(e)}")
            return jsonify({"error": error_msg}), 401
        
        if not is_valid:
            logger.warning(f"Tentativa de login com senha incorreta para: {email}")
            return jsonify({"error": error_msg}), 401

        # Gerar token de acesso
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "name": user.name,
                "email": user.email
            }
        )

        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,  # 1 hora em segundos
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro ao realizar login"}), 500


# ======================
# SAÚDE DO MÓDULO AUTH - CORRIGIDO
# ======================
@auth_bp.route("/health", methods=["GET"])
def auth_health():
    """Endpoint de saúde específico para o módulo de auth"""
    try:
        # Testar conexão com banco de forma segura
        try:
            user_count = User.query.limit(1).count()
            db_status = "connected"
        except Exception as db_error:
            logger.error(f"Erro de banco no health check: {str(db_error)}")
            db_status = f"error: {str(db_error)}"
            user_count = 0
        
        # Testar bcrypt
        try:
            test_hash = bcrypt.generate_password_hash(b"test").decode('utf-8')
            bcrypt_status = "available"
        except Exception as bcrypt_error:
            logger.error(f"Erro bcrypt no health check: {str(bcrypt_error)}")
            bcrypt_status = f"error: {str(bcrypt_error)}"
        
        return jsonify({
            "status": "healthy",
            "module": "authentication",
            "database": db_status,
            "bcrypt": bcrypt_status,
            "jwt": "available",
            "users_in_db": user_count
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no health check do auth: {str(e)}", exc_info=True)
        # Retornar erro sem tentar decode problemático
        return jsonify({
            "status": "unhealthy",
            "module": "authentication",
            "error": "Internal server error"
        }), 500


# ======================
# RESET DE SENHA (PARA TESTES)
# ======================
@auth_bp.route("/reset-test-user", methods=["POST"])
def reset_test_user():
    """Endpoint para resetar/criar usuário de teste (apenas desenvolvimento)"""
    if not current_app.config.get('DEBUG', False):
        return jsonify({"error": "Apenas em desenvolvimento"}), 403
    
    try:
        email = "test@example.com"
        password = "senha123"
        
        # Verificar se usuário existe
        user = User.query.filter_by(email=email).first()
        
        # Criar hash da senha
        password_hash = bcrypt.generate_password_hash(password.encode('utf-8')).decode('utf-8')
        
        if user:
            # Atualizar senha
            user.password_hash = password_hash
            logger.info(f"Senha resetada para usuário: {email}")
        else:
            # Criar novo usuário
            user = User(
                name="Usuário Teste",
                email=email,
                password_hash=password_hash
            )
            db.session.add(user)
            logger.info(f"Usuário de teste criado: {email}")
        
        db.session.commit()
        
        return jsonify({
            "message": "Usuário de teste configurado",
            "email": email,
            "password": password,
            "note": "Use estas credenciais para teste"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao resetar usuário de teste: {str(e)}")
        return jsonify({"error": "Erro ao configurar usuário de teste"}), 500