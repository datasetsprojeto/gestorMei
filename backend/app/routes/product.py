from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.monthly_snapshot import MonthlySnapshot
from app.models.audit_log import AuditLog
from app.models.user import User
from app.security import verify_owner_password
from app.services.audit_service import log_audit
from datetime import UTC, datetime

product_bp = Blueprint("products", __name__, url_prefix="/products")


def _workspace_owner_id(current_user_id):
    user = db.session.get(User, current_user_id)
    if not user:
        return None
    return user.owner_id if user.owner_id else user.id


def _parse_iso_datetime(value, label):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            return dt.astimezone(UTC).replace(tzinfo=None)
        return dt
    except Exception:
        raise ValueError(f"{label} inválida")


# ======================
# LISTAR PRODUTOS
# ======================
@product_bp.route("/", methods=["GET"])
@jwt_required()
def list_products():
    try:
        current_user_id = int(get_jwt_identity())
        user_id = _workspace_owner_id(current_user_id)
        if not user_id:
            return jsonify({"error": "Usuário não encontrado"}), 404

        # Opção de busca por nome
        search = request.args.get("search", "").strip()
        
        query = Product.query.filter_by(user_id=user_id, is_active=True)
        
        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))
        
        # Ordenação
        order_by = request.args.get("order_by", "name")
        order_dir = request.args.get("order_dir", "asc")
        
        if order_by == "price":
            if order_dir.lower() == "desc":
                query = query.order_by(Product.price.desc())
            else:
                query = query.order_by(Product.price.asc())
        else:
            if order_dir.lower() == "desc":
                query = query.order_by(Product.name.desc())
            else:
                query = query.order_by(Product.name.asc())
        
        products = query.all()
        
        # Paginação (simples)
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        total = len(products)
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_products = products[start_idx:end_idx]

        return jsonify({
            "products": [p.to_dict() for p in paginated_products],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro ao listar produtos: {str(e)}"}), 500


# ======================
# OBTER PRODUTO POR ID
# ======================
@product_bp.route("/<int:product_id>", methods=["GET"])
@jwt_required()
def get_product(product_id):
    try:
        current_user_id = int(get_jwt_identity())
        user_id = _workspace_owner_id(current_user_id)
        if not user_id:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        product = Product.query.filter_by(id=product_id, user_id=user_id, is_active=True).first()
        
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404
        
        return jsonify(product.to_dict()), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro ao obter produto: {str(e)}"}), 500


# ======================
# CRIAR PRODUTO
# ======================
@product_bp.route("/", methods=["POST"])
@jwt_required()
def create_product():
    try:
        current_user_id = int(get_jwt_identity())
        user_id = _workspace_owner_id(current_user_id)
        if not user_id:
            return jsonify({"error": "Usuário não encontrado"}), 404
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400

        name = data.get("name")
        price = data.get("price")
        cost = data.get("cost", 0)
        stock = data.get("stock", 0)
        min_stock = data.get("min_stock", 10)
        max_stock = data.get("max_stock", 100)

        # Validações
        if not name or price is None:
            return jsonify({"error": "Nome e preço são obrigatórios"}), 400
        
        if not isinstance(name, str) or len(name.strip()) < 2:
            return jsonify({"error": "Nome deve ter pelo menos 2 caracteres"}), 400
        
        try:
            price = float(price)
            if price < 0:
                return jsonify({"error": "Preço não pode ser negativo"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Preço deve ser um número válido"}), 400

        try:
            cost = float(cost)
            if cost < 0:
                return jsonify({"error": "Custo não pode ser negativo"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Custo deve ser um número válido"}), 400
        
        try:
            stock = int(stock)
            if stock < 0:
                return jsonify({"error": "Estoque não pode ser negativo"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Estoque deve ser um número inteiro"}), 400

        try:
            min_stock = int(min_stock)
            if min_stock < 0:
                return jsonify({"error": "Estoque mínimo não pode ser negativo"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Estoque mínimo inválido"}), 400

        try:
            max_stock = int(max_stock)
            if max_stock <= 0:
                return jsonify({"error": "Estoque máximo deve ser maior que zero"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Estoque máximo inválido"}), 400

        if min_stock > max_stock:
            return jsonify({"error": "Estoque mínimo não pode ser maior que o máximo"}), 400

        # Verificar se produto com mesmo nome já existe
        existing_product = Product.query.filter_by(
            name=name.strip(),
            user_id=user_id,
            is_active=True
        ).first()
        
        if existing_product:
            return jsonify({"error": "Já existe um produto com este nome"}), 409

        # Criar produto
        product = Product(
            name=name.strip(),
            price=price,
            cost=cost,
            stock=stock,
            min_stock=min_stock,
            max_stock=max_stock,
            user_id=user_id
        )

        db.session.add(product)
        db.session.commit()

        return jsonify({
            "message": "Produto criado com sucesso",
            "product": product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao criar produto: {str(e)}"}), 500


# ======================
# ATUALIZAR PRODUTO
# ======================
@product_bp.route("/<int:product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id):
    try:
        current_user_id = int(get_jwt_identity())
        user_id = _workspace_owner_id(current_user_id)
        if not user_id:
            return jsonify({"error": "Usuário não encontrado"}), 404
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400

        product = Product.query.filter_by(id=product_id, user_id=user_id, is_active=True).first()
        
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404
        
        # Validações e atualizações
        updates = {}
        
        if "name" in data:
            new_name = data["name"].strip()
            if len(new_name) < 2:
                return jsonify({"error": "Nome deve ter pelo menos 2 caracteres"}), 400
            
            # Verificar se outro produto já tem este nome
            existing = Product.query.filter(
                Product.id != product_id,
                Product.name == new_name,
                Product.user_id == user_id
            ).first()
            
            if existing:
                return jsonify({"error": "Já existe outro produto com este nome"}), 409
            
            product.name = new_name
        
        if "price" in data:
            try:
                new_price = float(data["price"])
                if new_price < 0:
                    return jsonify({"error": "Preço não pode ser negativo"}), 400
                product.price = new_price
            except (ValueError, TypeError):
                return jsonify({"error": "Preço inválido"}), 400

        if "cost" in data:
            try:
                new_cost = float(data["cost"])
                if new_cost < 0:
                    return jsonify({"error": "Custo não pode ser negativo"}), 400
                product.cost = new_cost
            except (ValueError, TypeError):
                return jsonify({"error": "Custo inválido"}), 400
        
        if "stock" in data:
            try:
                new_stock = int(data["stock"])
                if new_stock < 0:
                    return jsonify({"error": "Estoque não pode ser negativo"}), 400
                product.stock = new_stock
            except (ValueError, TypeError):
                return jsonify({"error": "Estoque inválido"}), 400

        if "min_stock" in data:
            try:
                new_min_stock = int(data["min_stock"])
                if new_min_stock < 0:
                    return jsonify({"error": "Estoque mínimo não pode ser negativo"}), 400
                product.min_stock = new_min_stock
            except (ValueError, TypeError):
                return jsonify({"error": "Estoque mínimo inválido"}), 400

        if "max_stock" in data:
            try:
                new_max_stock = int(data["max_stock"])
                if new_max_stock <= 0:
                    return jsonify({"error": "Estoque máximo deve ser maior que zero"}), 400
                product.max_stock = new_max_stock
            except (ValueError, TypeError):
                return jsonify({"error": "Estoque máximo inválido"}), 400

        if product.min_stock > product.max_stock:
            return jsonify({"error": "Estoque mínimo não pode ser maior que o máximo"}), 400

        db.session.commit()
        
        return jsonify({
            "message": "Produto atualizado com sucesso",
            "product": product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao atualizar produto: {str(e)}"}), 500


# ======================
# REGISTRAR ENTRADA DE MERCADORIA
# ======================
@product_bp.route("/entries", methods=["POST"])
@jwt_required()
def create_stock_entry():
    try:
        current_user_id = int(get_jwt_identity())
        user_id = _workspace_owner_id(current_user_id)
        if not user_id:
            return jsonify({"error": "Usuário não encontrado"}), 404

        data = request.get_json(silent=True) or {}
        product_id = data.get("product_id")
        quantity = data.get("quantity")
        unit_cost = data.get("unit_cost", 0)
        supplier = str(data.get("supplier", "")).strip()
        invoice = str(data.get("invoice", "")).strip()

        if not product_id or quantity is None:
            return jsonify({"error": "Produto e quantidade são obrigatórios"}), 400

        try:
            product_id = int(product_id)
        except (ValueError, TypeError):
            return jsonify({"error": "Produto inválido"}), 400

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return jsonify({"error": "Quantidade deve ser maior que zero"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Quantidade inválida"}), 400

        try:
            unit_cost = float(unit_cost)
            if unit_cost < 0:
                return jsonify({"error": "Custo unitário não pode ser negativo"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Custo unitário inválido"}), 400

        product = Product.query.filter_by(id=product_id, user_id=user_id, is_active=True).with_for_update().first()
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404

        base_product_id = int(product.id)
        base_product_name = product.name
        base_product_cost = float(product.cost or 0)
        effective_unit_cost = unit_cost if unit_cost > 0 else base_product_cost
        variant_created = False
        variant_id = None

        if abs(effective_unit_cost - base_product_cost) > 0.0001:
            variant_name = f"{base_product_name} (custo {effective_unit_cost:.2f})"
            variant = Product.query.filter_by(
                name=variant_name,
                user_id=user_id,
                is_active=True,
            ).with_for_update().first()

            if not variant:
                variant = Product(
                    name=variant_name,
                    price=float(product.price or 0),
                    cost=effective_unit_cost,
                    stock=0,
                    min_stock=int(product.min_stock or 0),
                    max_stock=int(product.max_stock or 100),
                    user_id=user_id,
                )
                db.session.add(variant)
                db.session.flush()
                variant_created = True

            product = variant
            variant_id = int(variant.id)
            unit_cost = effective_unit_cost

        before_stock = int(product.stock or 0)
        product.stock = before_stock + quantity
        if unit_cost > 0:
            product.cost = unit_cost

        total_cost = unit_cost * quantity
        details = {
            "base_product_id": base_product_id,
            "base_product_name": base_product_name,
            "product_id": product.id,
            "product_name": product.name,
            "quantity": quantity,
            "unit_cost": unit_cost,
            "total_cost": total_cost,
            "supplier": supplier,
            "invoice": invoice,
            "stock_before": before_stock,
            "stock_after": int(product.stock),
            "variant_created": variant_created,
            "variant_id": variant_id,
        }

        log_audit(
            owner_id=user_id,
            actor_user_id=current_user_id,
            action="product.stock_entry",
            resource_type="product",
            resource_id=str(product.id),
            details=details,
        )

        db.session.commit()

        saved_entry = AuditLog.query.filter(
            AuditLog.owner_id == user_id,
            AuditLog.action == "product.stock_entry",
            AuditLog.resource_id == str(product.id),
        ).order_by(AuditLog.id.desc()).first()
        created_at = saved_entry.created_at.isoformat() if saved_entry and saved_entry.created_at else None

        return jsonify({
            "message": "Entrada registrada com sucesso",
            "entry": {
                "created_at": created_at,
                "base_product_id": base_product_id,
                "base_product_name": base_product_name,
                "product_id": product.id,
                "product_name": product.name,
                "quantity": quantity,
                "unit_cost": unit_cost,
                "total_cost": total_cost,
                "supplier": supplier,
                "invoice": invoice,
                "stock_before": before_stock,
                "stock_after": int(product.stock),
                "variant_created": variant_created,
                "variant_id": variant_id,
            },
            "product": product.to_dict(),
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao registrar entrada: {str(e)}"}), 500


# ======================
# LISTAR ENTRADAS DE MERCADORIA
# ======================
@product_bp.route("/entries", methods=["GET"])
@jwt_required()
def list_stock_entries():
    try:
        current_user_id = int(get_jwt_identity())
        user_id = _workspace_owner_id(current_user_id)
        if not user_id:
            return jsonify({"error": "Usuário não encontrado"}), 404

        limit = min(500, max(1, int(request.args.get("limit", 200))))
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        product_id = request.args.get("product_id")

        query = AuditLog.query.filter(
            AuditLog.owner_id == user_id,
            AuditLog.action == "product.stock_entry",
        )

        if start_date:
            try:
                start_dt = _parse_iso_datetime(start_date, "Data inicial")
            except ValueError as err:
                return jsonify({"error": str(err)}), 400
            query = query.filter(AuditLog.created_at >= start_dt)

        if end_date:
            try:
                end_dt = _parse_iso_datetime(end_date, "Data final")
            except ValueError as err:
                return jsonify({"error": str(err)}), 400
            query = query.filter(AuditLog.created_at <= end_dt)

        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        parsed = []
        total_quantity = 0
        total_cost = 0.0

        for log in logs:
            details = log.get_details() or {}
            if product_id and str(details.get("product_id")) != str(product_id):
                continue

            qty = int(details.get("quantity") or 0)
            line_cost = float(details.get("total_cost") or 0)
            total_quantity += qty
            total_cost += line_cost

            parsed.append({
                "id": log.id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "product_id": details.get("product_id"),
                "product_name": details.get("product_name") or "Sem produto",
                "quantity": qty,
                "unit_cost": float(details.get("unit_cost") or 0),
                "total_cost": line_cost,
                "supplier": details.get("supplier") or "",
                "invoice": details.get("invoice") or "",
                "stock_before": details.get("stock_before"),
                "stock_after": details.get("stock_after"),
                "actor_user_id": log.actor_user_id,
            })

        return jsonify({
            "entries": parsed,
            "summary": {
                "total_entries": len(parsed),
                "total_quantity": total_quantity,
                "total_cost": total_cost,
            },
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao listar entradas: {str(e)}"}), 500


# ======================
# EXCLUIR PRODUTO
# ======================
@product_bp.route("/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):
    try:
        current_user_id = int(get_jwt_identity())
        user_id = _workspace_owner_id(current_user_id)
        if not user_id:
            return jsonify({"error": "Usuário não encontrado"}), 404
        force_delete = request.args.get("force", "false").strip().lower() == "true"
        data = request.get_json(silent=True) or {}
        owner_password = str(data.get("owner_password", "")).strip()

        current_user = db.session.get(User, current_user_id)
        ok_password, owner_user, password_error = verify_owner_password(current_user, owner_password)
        if not ok_password:
            return jsonify({"error": password_error}), 403
        
        product = Product.query.filter_by(id=product_id, user_id=user_id).first()
        
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404

        if not product.is_active:
            return jsonify({"error": "Produto já está arquivado"}), 400
        
        # Verificar se o produto tem vendas associadas
        if product.sale_items:
            product.is_active = False
            product.stock = 0
            log_audit(
                owner_id=owner_user.id,
                actor_user_id=current_user_id,
                action="product.archive",
                resource_type="product",
                resource_id=str(product_id),
                details={"reason": "has_sales", "sales_count": len(product.sale_items)},
            )
            db.session.commit()
            return jsonify({
                "message": "Produto arquivado com sucesso (mantido no histórico de vendas)",
                "product_id": product_id,
                "archived": True,
                "sales_count": len(product.sale_items)
            }), 200

        if product.stock > 0 and not force_delete:
            return jsonify({
                "error": "Produto ainda possui estoque. Confirme exclusão permanente.",
                "requires_force": True,
                "current_stock": int(product.stock)
            }), 409

        log_audit(
            owner_id=owner_user.id,
            actor_user_id=current_user_id,
            action="product.delete",
            resource_type="product",
            resource_id=str(product_id),
            details={"force_delete": bool(force_delete), "product_name": product.name},
        )
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            "message": "Produto excluído com sucesso",
            "product_id": product_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao excluir produto: {str(e)}"}), 500


# ======================
# LIMPAR CACHE DE DADOS DO NEGÓCIO
# ======================
@product_bp.route("/cache/clear-data", methods=["POST"])
@jwt_required()
def clear_workspace_data_cache():
    try:
        current_user_id = int(get_jwt_identity())
        current_user = db.session.get(User, current_user_id)
        if not current_user:
            return jsonify({"error": "Usuário não encontrado"}), 404

        if current_user.owner_id is not None:
            return jsonify({"error": "Somente o proprietário pode limpar os dados."}), 403

        data = request.get_json(silent=True) or {}
        owner_password = str(data.get("owner_password", "")).strip()
        ok_password, owner_user, password_error = verify_owner_password(current_user, owner_password)
        if not ok_password:
            return jsonify({"error": password_error}), 403

        owner_id = current_user.id

        sale_ids_subquery = db.session.query(Sale.id).filter(Sale.user_id == owner_id).subquery()

        deleted_sale_items = SaleItem.query.filter(
            SaleItem.sale_id.in_(db.session.query(sale_ids_subquery.c.id))
        ).delete(synchronize_session=False)

        deleted_sales = Sale.query.filter(Sale.user_id == owner_id).delete(synchronize_session=False)
        deleted_products = Product.query.filter(Product.user_id == owner_id).delete(synchronize_session=False)
        deleted_snapshots = MonthlySnapshot.query.filter(
            MonthlySnapshot.user_id == owner_id
        ).delete(synchronize_session=False)

        log_audit(
            owner_id=owner_user.id,
            actor_user_id=current_user_id,
            action="workspace.clear_operational_data",
            resource_type="workspace",
            resource_id=str(owner_id),
            details={
                "deleted_sale_items": int(deleted_sale_items or 0),
                "deleted_sales": int(deleted_sales or 0),
                "deleted_products": int(deleted_products or 0),
                "deleted_monthly_snapshots": int(deleted_snapshots or 0),
            },
        )

        db.session.commit()

        return jsonify({
            "message": "Dados operacionais limpos com sucesso. Usuários foram preservados.",
            "deleted": {
                "sale_items": int(deleted_sale_items or 0),
                "sales": int(deleted_sales or 0),
                "products": int(deleted_products or 0),
                "monthly_snapshots": int(deleted_snapshots or 0),
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao limpar dados operacionais: {str(e)}"}), 500