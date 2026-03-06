from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo

from app import create_app
from app.extensions import db, bcrypt
from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.monthly_snapshot import MonthlySnapshot


def ensure_admin():
    admin = User.query.filter_by(email="admin@gestormei.com").first()
    if admin:
        return admin

    password_hash = bcrypt.generate_password_hash("admin123".encode("utf-8")).decode("utf-8")
    admin = User(name="Administrador", email="admin@gestormei.com", phone="", password_hash=password_hash)
    db.session.add(admin)
    db.session.commit()
    return admin


def reset_products_and_sales(owner_id):
    # Limpa apenas dados transacionais solicitados: vendas, itens e produtos.
    SaleItem.query.delete()
    Sale.query.delete()
    Product.query.filter_by(user_id=owner_id).delete()
    MonthlySnapshot.query.filter_by(user_id=owner_id).delete()
    db.session.commit()


def seed_simulation(owner_id):
    product = Product(
        name="Calcinha Vermelha",
        price=35.0,
        cost=25.0,
        stock=50,
        min_stock=10,
        max_stock=100,
        is_active=True,
        user_id=owner_id,
    )
    db.session.add(product)
    db.session.flush()

    sale = Sale(total=35.0, user_id=owner_id, employee_id=owner_id)
    db.session.add(sale)
    db.session.flush()

    item = SaleItem(
        sale_id=sale.id,
        product_id=product.id,
        quantity=1,
        price=35.0,
        unit_cost=25.0,
    )
    db.session.add(item)

    product.stock -= 1
    db.session.commit()


def run_check(owner_id):
    business_tz = ZoneInfo("America/Sao_Paulo")
    utc_tz = ZoneInfo("UTC")

    now_local = datetime.now(business_tz)

    day_local_start = datetime.combine(now_local.date(), dt_time.min, tzinfo=business_tz)
    day_local_end = day_local_start + timedelta(days=1)
    day_start = day_local_start.astimezone(utc_tz).replace(tzinfo=None)
    day_end = day_local_end.astimezone(utc_tz).replace(tzinfo=None)

    month_local_start = datetime(now_local.year, now_local.month, 1, tzinfo=business_tz)
    if now_local.month == 12:
        month_local_end = datetime(now_local.year + 1, 1, 1, tzinfo=business_tz)
    else:
        month_local_end = datetime(now_local.year, now_local.month + 1, 1, tzinfo=business_tz)

    month_start = month_local_start.astimezone(utc_tz).replace(tzinfo=None)
    month_end = month_local_end.astimezone(utc_tz).replace(tzinfo=None)

    day_gross = db.session.query(db.func.sum(Sale.total)).filter(
        Sale.user_id == owner_id,
        Sale.created_at >= day_start,
        Sale.created_at < day_end,
    ).scalar() or 0

    day_net = db.session.query(
        db.func.sum((SaleItem.price - db.func.coalesce(db.func.nullif(SaleItem.unit_cost, 0), Product.cost, 0)) * SaleItem.quantity)
    ).join(Sale, Sale.id == SaleItem.sale_id).join(Product, Product.id == SaleItem.product_id).filter(
        Sale.user_id == owner_id,
        Sale.created_at >= day_start,
        Sale.created_at < day_end,
    ).scalar() or 0

    month_gross = db.session.query(db.func.sum(Sale.total)).filter(
        Sale.user_id == owner_id,
        Sale.created_at >= month_start,
        Sale.created_at < month_end,
    ).scalar() or 0

    month_net = db.session.query(
        db.func.sum((SaleItem.price - db.func.coalesce(db.func.nullif(SaleItem.unit_cost, 0), Product.cost, 0)) * SaleItem.quantity)
    ).join(Sale, Sale.id == SaleItem.sale_id).join(Product, Product.id == SaleItem.product_id).filter(
        Sale.user_id == owner_id,
        Sale.created_at >= month_start,
        Sale.created_at < month_end,
    ).scalar() or 0

    print("SIMULACAO CONCLUIDA")
    print("Esperado -> Hoje Liquido: 10.00 | Hoje Bruto: 35.00 | Mes Liquido: 10.00 | Mes Bruto: 35.00")
    print(f"Obtido   -> Hoje Liquido: {float(day_net):.2f} | Hoje Bruto: {float(day_gross):.2f} | Mes Liquido: {float(month_net):.2f} | Mes Bruto: {float(month_gross):.2f}")


def main():
    app = create_app("development")
    with app.app_context():
        admin = ensure_admin()
        owner_id = admin.owner_id if admin.owner_id else admin.id

        reset_products_and_sales(owner_id)
        seed_simulation(owner_id)
        run_check(owner_id)


if __name__ == "__main__":
    main()
