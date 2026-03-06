from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
import secrets
import string

from app.extensions import db, bcrypt
from app.models.user import User
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.product import Product

employee_bp = Blueprint("employees", __name__, url_prefix="/employees")


def _effective_unit_cost(func_obj):
    return func_obj.coalesce(func_obj.nullif(SaleItem.unit_cost, 0), Product.cost, 0)


def _get_current_user():
    current_user_id = int(get_jwt_identity())
    return User.query.get(current_user_id)


def _owner_workspace_id(user):
    return user.owner_id if user.owner_id else user.id


def _generate_temporary_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@employee_bp.route("/", methods=["GET"])
@jwt_required()
def list_employees():
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    owner_id = _owner_workspace_id(user)
    owner = User.query.get(owner_id)
    if not owner:
        return jsonify({"error": "Proprietário não encontrado"}), 404

    employees = User.query.filter_by(owner_id=owner.id).order_by(User.name.asc()).all()

    return jsonify({
        "owner": owner.to_dict(),
        "employees": [emp.to_dict() for emp in employees],
    }), 200


@employee_bp.route("/link", methods=["POST"])
@jwt_required()
def link_employee():
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    # Somente proprietário pode vincular funcionários.
    if user.owner_id is not None:
        return jsonify({"error": "Apenas o proprietário pode vincular funcionários."}), 403

    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    employee_name = str(data.get("name", "")).strip()
    employee_phone = str(data.get("phone", "")).strip()

    if not email:
        return jsonify({"error": "E-mail do funcionário é obrigatório."}), 400

    employee = User.query.filter_by(email=email).first()
    generated_password = None
    if not employee:
        if not employee_name:
            employee_name = email.split("@")[0].replace(".", " ").replace("_", " ").title() or "Funcionário"

        generated_password = _generate_temporary_password()
        password_hash = bcrypt.generate_password_hash(generated_password.encode("utf-8")).decode("utf-8")
        employee = User(
            name=employee_name,
            email=email,
            phone=employee_phone,
            password_hash=password_hash,
        )
        db.session.add(employee)
        db.session.flush()

    if employee.id == user.id:
        return jsonify({"error": "Não é possível vincular o próprio proprietário como funcionário."}), 400

    if employee.owner_id and employee.owner_id != user.id:
        return jsonify({"error": "Este funcionário já está vinculado a outro proprietário."}), 409

    employee.owner_id = user.id
    db.session.commit()

    response = {
        "message": "Funcionário vinculado com sucesso.",
        "employee": employee.to_dict(),
    }
    if generated_password:
        response["generated_password"] = generated_password
        response["message"] = "Funcionário criado e vinculado com sucesso. Compartilhe a senha temporária."

    return jsonify(response), 200


@employee_bp.route("/unlink/<int:employee_id>", methods=["POST"])
@jwt_required()
def unlink_employee(employee_id):
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    if user.owner_id is not None:
        return jsonify({"error": "Apenas o proprietário pode desvincular funcionários."}), 403

    employee = User.query.filter_by(id=employee_id, owner_id=user.id).first()
    if not employee:
        return jsonify({"error": "Funcionário vinculado não encontrado."}), 404

    employee.owner_id = None
    db.session.commit()

    return jsonify({
        "message": "Funcionário desvinculado com sucesso.",
        "employee": employee.to_dict(),
    }), 200


@employee_bp.route("/analytics", methods=["GET"])
@jwt_required()
def employee_analytics():
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    owner_id = _owner_workspace_id(user)
    now = datetime.utcnow()
    days = int(request.args.get("days", 30))
    start_date = now - timedelta(days=days)

    sales_grouped = db.session.query(
        func.coalesce(Sale.employee_id, owner_id).label("employee_id"),
        func.count(Sale.id).label("sales_count"),
        func.sum(Sale.total).label("gross_total"),
    ).filter(
        Sale.user_id == owner_id,
        Sale.created_at >= start_date,
    ).group_by(
        func.coalesce(Sale.employee_id, owner_id)
    ).all()

    net_grouped = db.session.query(
        func.coalesce(Sale.employee_id, owner_id).label("employee_id"),
        func.sum((SaleItem.price - _effective_unit_cost(func)) * SaleItem.quantity).label("net_total"),
    ).join(
        Sale, Sale.id == SaleItem.sale_id
    ).join(
        Product, Product.id == SaleItem.product_id
    ).filter(
        Sale.user_id == owner_id,
        Sale.created_at >= start_date,
    ).group_by(
        func.coalesce(Sale.employee_id, owner_id)
    ).all()

    net_by_employee = {int(emp_id): float(net_total or 0) for emp_id, net_total in net_grouped}

    employee_ids = set()
    analytics = []

    for emp_id, sales_count, gross_total in sales_grouped:
        emp_id_int = int(emp_id)
        employee_ids.add(emp_id_int)
        analytics.append({
            "employee_id": emp_id_int,
            "sales_count": int(sales_count or 0),
            "gross_total": float(gross_total or 0),
            "net_total": float(net_by_employee.get(emp_id_int, 0)),
        })

    # Inclui funcionários sem venda no período.
    linked_employees = User.query.filter_by(owner_id=owner_id).all()
    for emp in linked_employees:
        if emp.id not in employee_ids:
            analytics.append({
                "employee_id": emp.id,
                "sales_count": 0,
                "gross_total": 0.0,
                "net_total": 0.0,
            })

    name_by_id = {}
    owner = User.query.get(owner_id)
    if owner:
        name_by_id[owner_id] = owner.name
    for emp in linked_employees:
        name_by_id[emp.id] = emp.name

    analytics.sort(key=lambda row: row["gross_total"], reverse=True)

    return jsonify({
        "period": {
            "days": days,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat(),
        },
        "employees": [
            {
                **row,
                "employee_name": name_by_id.get(row["employee_id"], f"Funcionário #{row['employee_id']}"),
            }
            for row in analytics
        ],
    }), 200
