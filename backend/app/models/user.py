from app.extensions import db
from datetime import UTC, datetime


def utc_now():
    return datetime.now(UTC)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relações
    products = db.relationship("Product", backref="owner", lazy=True, cascade="all, delete-orphan")
    sales = db.relationship(
        "Sale",
        backref="owner",
        lazy=True,
        cascade="all, delete-orphan",
        foreign_keys="Sale.user_id",
    )
    employees = db.relationship("User", backref=db.backref("manager", remote_side=[id]), lazy=True)
    
    def to_dict(self):
        """Converter objeto para dicionário"""
        account_owner_id = self.owner_id if self.owner_id else self.id
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "owner_id": self.owner_id,
            "account_owner_id": account_owner_id,
            "is_owner": self.owner_id is None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }