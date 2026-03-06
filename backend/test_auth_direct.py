#!/usr/bin/env python
"""
Teste direto do módulo de autenticação
"""

import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db, bcrypt
from app.models.user import User

def test_auth_directly():
    """Testa o módulo de auth diretamente"""
    
    print("🧪 TESTE DIRETO DO MÓDULO DE AUTENTICAÇÃO")
    print("=" * 60)
    
    # Criar app de teste
    app = create_app("development")
    
    with app.app_context():
        try:
            # 1. Testar bcrypt
            print("\n1. Testando bcrypt...")
            test_password = "senha123"
            password_hash = bcrypt.generate_password_hash(test_password.encode('utf-8')).decode('utf-8')
            print(f"   Senha: {test_password}")
            print(f"   Hash gerado: {password_hash[:50]}...")
            
            # Verificar hash
            is_valid = bcrypt.check_password_hash(password_hash, test_password.encode('utf-8'))
            print(f"   Verificação: {'✅ Válido' if is_valid else '❌ Inválido'}")
            
            # 2. Testar criação de usuário
            print("\n2. Testando criação de usuário...")
            
            # Limpar qualquer usuário de teste anterior
            User.query.filter_by(email="teste_direto@email.com").delete()
            db.session.commit()
            
            # Criar usuário
            user = User(
                name="Teste Direto",
                email="teste_direto@email.com",
                password_hash=password_hash
            )
            
            db.session.add(user)
            db.session.commit()
            
            print(f"   Usuário criado: ID={user.id}, Email={user.email}")
            
            # 3. Buscar usuário
            print("\n3. Testando busca de usuário...")
            found_user = User.query.filter_by(email="teste_direto@email.com").first()
            
            if found_user:
                print(f"   Usuário encontrado: {found_user.name}")
                print(f"   Hash no banco: {found_user.password_hash[:50]}...")
                
                # 4. Verificar senha
                print("\n4. Testando verificação de senha...")
                correct_check = bcrypt.check_password_hash(found_user.password_hash, "senha123".encode('utf-8'))
                wrong_check = bcrypt.check_password_hash(found_user.password_hash, "senha_errada".encode('utf-8'))
                
                print(f"   Senha correta: {'✅' if correct_check else '❌'}")
                print(f"   Senha errada: {'✅ Rejeitada' if not wrong_check else '❌ Aceita (ERRO)'}")
                
            else:
                print("   ❌ Usuário não encontrado")
            
            # 5. Limpar
            print("\n5. Limpando dados de teste...")
            if found_user:
                db.session.delete(found_user)
                db.session.commit()
                print("   ✅ Usuário de teste removido")
            
            print("\n" + "=" * 60)
            print("🎉 Teste direto concluído com sucesso!")
            print("=" * 60)
            
            assert True
            
        except Exception as e:
            print(f"\n❌ Erro durante o teste: {str(e)}")
            import traceback
            traceback.print_exc()
            assert False, f"Erro durante o teste direto de auth: {str(e)}"

def test_email_validation():
    """Testa a validação de email"""
    
    print("\n📧 TESTANDO VALIDAÇÃO DE EMAIL")
    print("=" * 60)
    
    # Importar a função de validação
    from app.routes.auth import is_valid_email
    
    test_cases = [
        ("usuario@email.com", True),
        ("usuario.nome@empresa.com.br", True),
        ("usuario+tag@email.com", True),
        ("usuario@dominio", False),
        ("@email.com", False),
        ("usuario@", False),
        ("", False),
        (None, False),
        ("espaço @email.com", False),
        ("teste@192.168.1.1", False),  # IP não é permitido no padrão básico
    ]
    
    all_passed = True
    for email, expected in test_cases:
        result = is_valid_email(email)
        passed = result == expected
        
        status = "✅" if passed else "❌"
        print(f"{status} '{email}' -> Esperado: {expected}, Obtido: {result}")
        
        if not passed:
            all_passed = False
    
    assert all_passed, "Falha em um ou mais casos de validação de e-mail"

def test_password_validation():
    """Testa a validação de senha"""
    
    print("\n🔐 TESTANDO VALIDAÇÃO DE SENHA")
    print("=" * 60)
    
    # Importar a função de validação
    from app.routes.auth import validate_password
    
    test_cases = [
        ("senha123", None),  # Válida
        ("123456", None),    # Válida
        ("abc123", None),    # Válida
        ("short", "Senha deve ter pelo menos 6 caracteres"),
        ("", "Senha inválida"),
        (None, "Senha inválida"),
        ("senhasemnumeros", "Senha deve conter pelo menos um número"),
        ("SENHA123", None),  # Válida (tem números)
    ]
    
    all_passed = True
    for password, expected_error in test_cases:
        result = validate_password(password)
        passed = result == expected_error
        
        status = "✅" if passed else "❌"
        test_value = f"'{password}'" if password is not None else "None"
        
        if expected_error is None:
            print(f"{status} {test_value} -> Esperado: Válida, Obtido: {result or 'Válida'}")
        else:
            print(f"{status} {test_value} -> Esperado: '{expected_error}', Obtido: '{result}'")
        
        if not passed:
            all_passed = False
    
    assert all_passed, "Falha em um ou mais casos de validação de senha"

def main():
    """Função principal"""
    
    print("🔧 TESTE DO MÓDULO DE AUTENTICAÇÃO")
    print("=" * 60)
    
    tests = [
        ("Validação de Email", test_email_validation),
        ("Validação de Senha", test_password_validation),
        ("Teste Direto no Banco", test_auth_directly),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Executando: {test_name}")
        try:
            test_func()
            results.append((test_name, True))
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            results.append((test_name, False))
    
    # Resumo
    print(f"\n{'='*60}")
    print("📊 RESUMO DOS TESTES")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} passaram")
    
    if passed == total:
        print("\n🎉 Módulo de autenticação está funcionando corretamente!")
        print("\n🚀 Próximos passos:")
        print("   1. Inicie o servidor: python run.py")
        print("   2. Teste os endpoints com curl ou Postman")
        print("   3. Execute testes completos: python test_api_fixed.py")
    else:
        print("\n⚠️  Alguns testes falharam.")
        print("\n🔧 Soluções possíveis:")
        print("   1. Verifique se o PostgreSQL está instalado e rodando")
        print("   2. Execute as migrações: flask db upgrade")
        print("   3. Configure o .env corretamente")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)