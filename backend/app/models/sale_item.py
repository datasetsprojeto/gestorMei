from app.extensions import db

class SaleItem(db.Model):
    __tablename__ = "sale_items"

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    
    # Índices compostos para performance
    __table_args__ = (
        db.Index('idx_sale_product', 'sale_id', 'product_id'),
        db.Index('idx_product_sale', 'product_id', 'sale_id'),
    )
    
    def to_dict(self):
        """Converter objeto para dicionário"""
        unit_price = float(self.price)
        effective_unit_cost = float(self.unit_cost)
        if effective_unit_cost == 0 and self.product:
            effective_unit_cost = float(self.product.cost or 0)

        return {
            "id": self.id,
            "quantity": self.quantity,
            "price": unit_price,
            "unit_cost": effective_unit_cost,
            "subtotal": float(unit_price * self.quantity),
            "cost_subtotal": float(effective_unit_cost * self.quantity),
            "profit_subtotal": float((unit_price - effective_unit_cost) * self.quantity),
            "sale_id": self.sale_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None
        }