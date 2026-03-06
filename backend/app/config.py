import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_SQLITE_PATH = DATA_DIR / "gestormei.db"

class Config:
    """Configurações base"""
    
    # Segurança
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Banco de Dados
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-super-secret-key-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Aplicação
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    # Configurações de segurança
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # SMTP / E-mail
    SMTP_HOST = os.getenv("SMTP_HOST") or os.getenv("MAIL_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT") or os.getenv("MAIL_PORT") or 587)
    SMTP_USERNAME = os.getenv("SMTP_USERNAME") or os.getenv("MAIL_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or os.getenv("MAIL_PASSWORD")
    SMTP_USE_TLS = (os.getenv("SMTP_USE_TLS") or os.getenv("MAIL_USE_TLS") or "true").lower() == "true"
    SMTP_USE_SSL = (os.getenv("SMTP_USE_SSL") or os.getenv("MAIL_USE_SSL") or "false").lower() == "true"
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL") or os.getenv("MAIL_DEFAULT_SENDER") or SMTP_USERNAME
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME") or "VendaMais"
    
    # Rate limiting (se implementado no futuro)
    RATELIMIT_ENABLED = os.getenv("RATELIMIT_ENABLED", "False").lower() == "true"
    
    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # Confirmação de exclusão de produtos
    OWNER_DELETE_PASSWORD = os.getenv("OWNER_DELETE_PASSWORD", "senha123")


class DevelopmentConfig(Config):
    """Configurações de desenvolvimento"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Configurações de teste"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(Config):
    """Configurações de produção"""
    
    def __init__(self):
        super().__init__()
        
        self.DEBUG = False
        self.SESSION_COOKIE_SECURE = True
        
        # Em produção, verificar se variáveis de ambiente estão definidas
        if not self.SECRET_KEY or self.SECRET_KEY.startswith("dev-secret-key"):
            raise ValueError("SECRET_KEY deve ser definida em produção")
        
        if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY.startswith("jwt-super-secret-key"):
            raise ValueError("JWT_SECRET_KEY deve ser definida em produção")


# Mapeamento de configurações
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}