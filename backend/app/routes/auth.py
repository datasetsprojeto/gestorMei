from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.extensions import db, bcrypt
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.audit_service import log_audit
from app.services.email_service import send_password_email, EmailServiceError
import re
import logging
import secrets
import string
from datetime import UTC, datetime, timedelta

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Configurar logger específico para auth
logger = logging.getLogger(__name__)

_LOGIN_ATTEMPTS = {}
_MAX_LOGIN_ATTEMPTS = 5
_LOGIN_WINDOW_MINUTES = 15


def _workspace_owner_id(user):
    if not user:
        return None
    return user.owner_id if user.owner_id else user.id


def _login_attempt_key(email):
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    return f"{ip}|{email}"


def _is_login_rate_limited(email):
    key = _login_attempt_key(email)
    state = _LOGIN_ATTEMPTS.get(key)
    now = datetime.now(UTC)
    if not state:
        return False, 0

    reset_at = state.get("reset_at")
    if not reset_at or now >= reset_at:
        _LOGIN_ATTEMPTS.pop(key, None)
        return False, 0

    attempts = int(state.get("count", 0))
    remaining = max(0, _MAX_LOGIN_ATTEMPTS - attempts)
    return attempts >= _MAX_LOGIN_ATTEMPTS, remaining


def _register_login_attempt(email):
    key = _login_attempt_key(email)
    now = datetime.now(UTC)
    state = _LOGIN_ATTEMPTS.get(key)
    if not state or now >= state.get("reset_at", now):
        _LOGIN_ATTEMPTS[key] = {
            "count": 1,
            "reset_at": now + timedelta(minutes=_LOGIN_WINDOW_MINUTES),
        }
        return
    state["count"] = int(state.get("count", 0)) + 1


def _clear_login_attempts(email):
    key = _login_attempt_key(email)
    _LOGIN_ATTEMPTS.pop(key, None)

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


def validate_password(password):
    if password is None:
        return "Senha inválida"
    password = str(password)
    if not password:
        return "Senha inválida"
    if len(password) < 8:
        return "Senha deve ter pelo menos 8 caracteres"
    if not any(ch.isupper() for ch in password):
        return "Senha deve conter pelo menos uma letra maiúscula"
    if not any(ch.islower() for ch in password):
        return "Senha deve conter pelo menos uma letra minúscula"
    if not any(ch.isdigit() for ch in password):
        return "Senha deve conter pelo menos um número"
    if not any(ch in "!@#$%^&*()-_=+[]{};:,.?/" for ch in password):
        return "Senha deve conter pelo menos um caractere especial"
    return None


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
        explicit_password = data.get("password")

        # Validações básicas
        if not name or not email:
            return jsonify({"error": "Nome e e-mail são obrigatórios"}), 400
        
        # Limpar e validar nome
        name = str(name).strip()
        if len(name) < 2:
            return jsonify({"error": "Nome deve ter pelo menos 2 caracteres"}), 400
        
        # Limpar e validar email
        email = str(email).strip().lower()
        if not is_valid_email(email):
            return jsonify({"error": "Email invalido"}), 400

        # Limpar e validar telefone (opcional)
        phone = normalize_phone(str(phone or ""))
        if phone and not is_valid_phone(phone):
            return jsonify({"error": "Telefone invalido"}), 400

        # Verificar se email já existe
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "Email já cadastrado"}), 409

        if explicit_password:
            password_error = validate_password(explicit_password)
            if password_error:
                return jsonify({"error": password_error}), 400
            password_str = str(explicit_password)
        else:
            # Fluxo padrão: senha gerada e enviada por e-mail.
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
            "message": "Conta criada com sucesso."
            if explicit_password else "Conta criada com sucesso. A senha foi enviada para o e-mail informado.",
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

        is_limited, remaining = _is_login_rate_limited(email)
        if is_limited:
            return jsonify({
                "error": "Muitas tentativas de login. Tente novamente em alguns minutos.",
                "remaining_attempts": remaining,
            }), 429
        
        # Validar formato do email
        if not is_valid_email(email):
            # Retorna 400 em vez de 401 para formato inválido
            return jsonify({"error": "Email inválido"}), 400
        
        # Buscar usuário
        user = User.query.filter_by(email=email).first()

        # Mensagem genérica para segurança
        error_msg = "Credenciais inválidas"
        
        if not user:
            _register_login_attempt(email)
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
            _register_login_attempt(email)
            owner_id = _workspace_owner_id(user)
            if owner_id:
                log_audit(
                    owner_id=owner_id,
                    actor_user_id=user.id,
                    action="auth.login_failed",
                    resource_type="auth",
                    resource_id=str(user.id),
                    details={"reason": "invalid_password"},
                )
            logger.warning(f"Tentativa de login com senha incorreta para: {email}")
            return jsonify({"error": error_msg}), 401

        _clear_login_attempts(email)

        # Gerar token de acesso
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "name": user.name,
                "email": user.email
            }
        )

        owner_id = _workspace_owner_id(user)
        if owner_id:
            log_audit(
                owner_id=owner_id,
                actor_user_id=user.id,
                action="auth.login_success",
                resource_type="auth",
                resource_id=str(user.id),
                details={"email": user.email},
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


@auth_bp.route("/audit-logs", methods=["GET"])
@jwt_required()
def list_audit_logs():
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    if user.owner_id is not None:
        return jsonify({"error": "Apenas o proprietário pode visualizar auditoria."}), 403

    limit = min(500, max(1, int(request.args.get("limit", 100))))
    action = str(request.args.get("action", "")).strip()

    query = AuditLog.query.filter_by(owner_id=user.id)
    if action:
        query = query.filter(AuditLog.action == action)

    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return jsonify({"logs": [entry.to_dict() for entry in logs]}), 200


@auth_bp.route("/test", methods=["GET"])
def auth_test():
    return jsonify({"status": "ok", "module": "auth"}), 200


@auth_bp.route("/verify", methods=["GET"])
def auth_verify():
    # Endpoint de compatibilidade para verificações simples de disponibilidade.
    return jsonify({"status": "ok", "authenticated": False}), 200


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