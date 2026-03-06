#!/usr/bin/env python
"""
Script para resetar completamente o banco de dados
Útil quando há problemas de encoding ou dados corrompidos
"""

import os
import sys
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
import bcrypt as bcrypt_lib

def reset_database():
    """Resetar completamente o banco"""
    
    print("🔄 RESETANDO BANCO DE DADOS")
    print("=" * 60)
    
    # Criar app
    app = create_app("development")
    
    with app.app_context():
        try:
            # Confirmar ação
            print("⚠️  ATENÇÃO: Isso irá APAGAR TODOS os dados do banco!")
            print("   Todas as tabelas serão recriadas.")
            
            confirm = input("\nContinuar? (s/N): ").strip().lower()
            
            if confirm != 's':
                print("❌ Operação cancelada.")
                return False
            
            # 1. Deletar todas as tabelas
            print("\n1. 🗑️  Limpando banco de dados...")
            db.drop_all()
            print("   ✅ Tabelas removidas")
            
            # 2. Criar todas as tabelas
            print("\n2. 🏗️  Criando tabelas...")
            db.create_all()
            print("   ✅ Tabelas criadas")
            
            # 3. Criar usuário admin padrão com hash CORRETO
            print("\n3. 👤 Criando usuário admin...")
            
            # Criar hash CORRETAMENTE
            password = "admin123"
            password_bytes = password.encode('utf-8')
            
            # Usar bcrypt diretamente para garantir encoding correto
            salt = bcrypt_lib.gensalt()
            password_hash = bcrypt_lib.hashpw(password_bytes, salt)
            
            # Criar usuário
            admin_user = User(
                name="Administrador",
                email="admin@gestormei.com",
                password_hash=password_hash.decode('utf-8')  # Decodificar para string UTF-8
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print(f"   ✅ Usuário admin criado")
            print(f"   📧 Email: admin@gestormei.com")
            print(f"   🔑 Senha: admin123")
            print(f"   🔐 Hash (início): {admin_user.password_hash[:50]}...")
            
            # 4. Criar alguns produtos de exemplo
            print("\n4. 📦 Criando produtos de exemplo...")
            
            sample_products = [
                {"name": "Camiseta Básica", "price": 29.90, "stock": 100},
                {"name": "Calça Jeans", "price": 89.90, "stock": 50},
                {"name": "Tênis Esportivo", "price": 149.90, "stock": 30},
                {"name": "Boné", "price": 39.90, "stock": 80},
                {"name": "Mochila", "price": 79.90, "stock": 40},
            ]
            
            for product_data in sample_products:
                product = Product(
                    name=product_data["name"],
                    price=product_data["price"],
                    stock=product_data["stock"],
                    user_id=admin_user.id
                )
                db.session.add(product)
            
            db.session.commit()
            print("   ✅ 5 produtos de exemplo criados")
            
            # 5. Criar uma venda de exemplo
            print("\n5. 💰 Criando venda de exemplo...")
            
            # Buscar produtos
            products = Product.query.filter_by(user_id=admin_user.id).all()
            
            if len(products) >= 2:
                sale = Sale(
                    total=products[0].price * 2 + products[1].price * 1,
                    user_id=admin_user.id
                )
                
                db.session.add(sale)
                db.session.flush()  # Para obter o ID
                
                # Itens da venda
                sale_items = [
                    SaleItem(
                        sale_id=sale.id,
                        product_id=products[0].id,
                        quantity=2,
                        price=products[0].price
                    ),
                    SaleItem(
                        sale_id=sale.id,
                        product_id=products[1].id,
                        quantity=1,
                        price=products[1].price
                    )
                ]
                
                for item in sale_items:
                    db.session.add(item)
                
                # Atualizar estoque
                products[0].stock -= 2
                products[1].stock -= 1
                
                db.session.commit()
                print("   ✅ Venda de exemplo criada")
            
            print(f"\n{'='*60}")
            print("🎉 BANCO DE DADOS RESETADO COM SUCESSO!")
            print(f"{'='*60}")
            print("\n📋 DADOS DE TESTE:")
            print(f"   Usuário: admin@gestormei.com / admin123")
            print(f"   Produtos: 5 criados")
            print(f"   Vendas: 1 criada")
            print(f"\n🚀 Próximos passos:")
            print(f"   1. Inicie o servidor: python run.py")
            print(f"   2. Teste o login com as credenciais acima")
            print(f"   3. Execute: python test_auth_simple.py")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO ao resetar banco: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = reset_database()
    sys.exit(0 if success else 1)