from .health import health_bp
from .auth import auth_bp
from .product import product_bp
from .sale import sale_bp

__all__ = ['health_bp', 'auth_bp', 'product_bp', 'sale_bp']