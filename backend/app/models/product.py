from app.extensions import db
from datetime import UTC, datetime


def utc_now():
    return datetime.now(UTC)

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    min_stock = db.Column(db.Integer, nullable=False, default=10)
    max_stock = db.Column(db.Integer, nullable=False, default=100)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relações
    sale_items = db.relationship("SaleItem", backref="product", lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        """Converter objeto para dicionário"""
        return {
            "id": self.id,
            "name": self.name,
            "price": float(self.price),
            "cost": float(self.cost),
            "stock": self.stock,
            "min_stock": self.min_stock,
            "max_stock": self.max_stock,
            "is_active": self.is_active,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }