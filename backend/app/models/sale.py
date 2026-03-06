from app.extensions import db
from datetime import datetime

class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Relações
    items = db.relationship("SaleItem", backref="sale", lazy=True, cascade="all, delete-orphan")
    employee = db.relationship("User", foreign_keys=[employee_id], lazy="joined")
    
    def to_dict(self, include_items=False):
        """Converter objeto para dicionário"""
        total_items = sum(int(item.quantity or 0) for item in self.items)
        result = {
            "id": self.id,
            "total": float(self.total),
            "user_id": self.user_id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.name if self.employee else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "items_count": total_items
        }
        
        if include_items:
            result["items"] = [item.to_dict() for item in self.items]
            
        return result