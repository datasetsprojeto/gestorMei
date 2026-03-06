from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.product import Product
from app.models.user import User

product_bp = Blueprint("products", __name__, url_prefix="/products")


def _workspace_owner_id(current_user_id):
    user = User.query.get(current_user_id)
    if not user:
        return None
    return user.owner_id if user.owner_id else user.id


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
        expected_password = str(current_app.config.get("OWNER_DELETE_PASSWORD", "senha123")).strip()

        if owner_password != expected_password:
            return jsonify({"error": "Senha de proprietário inválida."}), 403
        
        product = Product.query.filter_by(id=product_id, user_id=user_id).first()
        
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404

        if not product.is_active:
            return jsonify({"error": "Produto já está arquivado"}), 400
        
        # Verificar se o produto tem vendas associadas
        if product.sale_items:
            product.is_active = False
            product.stock = 0
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
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            "message": "Produto excluído com sucesso",
            "product_id": product_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao excluir produto: {str(e)}"}), 500