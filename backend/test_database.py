# test_database.py
#!/usr/bin/env python
"""
Teste específico para verificar conexão com banco
"""

import sys
import os
from app import create_app
from app.extensions import db
from app.models.user import User

def test_database_connection():
    print("🔍 TESTANDO CONEXÃO COM BANCO DE DADOS")
    print("=" * 60)
    
    app = create_app("development")
    
    with app.app_context():
        try:
            # 1. Testar conexão básica
            print("\n1. Testando conexão com PostgreSQL...")
            result = db.session.execute("SELECT version()").fetchone()
            print(f"   ✅ PostgreSQL conectado: {result[0]}")
            
            # 2. Verificar tabelas
            print("\n2. Verificando tabelas...")
            tables = db.inspect(db.engine).get_table_names()
            print(f"   ✅ Tabelas encontradas: {len(tables)}")
            for table in tables:
                print(f"      - {table}")
            
            # 3. Verificar tabela users
            print("\n3. Verificando tabela users...")
            if 'users' in tables:
                user_count = User.query.count()
                print(f"   ✅ Tabela users existe com {user_count} usuário(s)")
                
                if user_count > 0:
                    users = User.query.limit(3).all()
                    for user in users:
                        print(f"      👤 {user.email} (ID: {user.id})")
                        # Verificar hash da senha
                        if user.password_hash:
                            print(f"         Hash: {user.password_hash[:30]}...")
            else:
                print("   ❌ Tabela users não existe!")
                
            # 4. Testar operações CRUD
            print("\n4. Testando operações CRUD...")
            try:
                # Criar usuário de teste
                from flask_bcrypt import generate_password_hash
                
                test_email = "test_db@email.com"
                
                # Limpar se existir
                User.query.filter_by(email=test_email).delete()
                db.session.commit()
                
                # Criar novo
                password_hash = generate_password_hash("test123").decode('utf-8')
                user = User(
                    name="Teste DB",
                    email=test_email,
                    password_hash=password_hash
                )
                
                db.session.add(user)
                db.session.commit()
                print(f"   ✅ Usuário criado: {test_email}")
                
                # Ler
                found = User.query.filter_by(email=test_email).first()
                print(f"   ✅ Usuário lido: {found.email if found else 'Não encontrado'}")
                
                # Deletar
                if found:
                    db.session.delete(found)
                    db.session.commit()
                    print(f"   ✅ Usuário deletado")
                
            except Exception as e:
                print(f"   ❌ Erro em operações CRUD: {str(e)}")
                import traceback
                traceback.print_exc()
            
            print(f"\n{'='*60}")
            print("🎉 CONEXÃO COM BANCO TESTADA COM SUCESSO!")
            print(f"{'='*60}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERRO na conexão com banco: {str(e)}")
            import traceback
            traceback.print_exc()
            
            print(f"\n🔧 SOLUÇÃO:")
            print(f"   1. Verifique se PostgreSQL está rodando")
            print(f"   2. Execute: python reset_database.py")
            print(f"   3. Verifique o arquivo .env")
            
            return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)