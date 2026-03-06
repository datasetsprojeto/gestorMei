#!/usr/bin/env python
"""
Script para debug do servidor Flask
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(filename):
    """Verifica se um arquivo existe"""
    return Path(filename).exists()

def check_directory_structure():
    """Verifica estrutura de diretórios"""
    print("📁 Verificando estrutura de diretórios...")
    
    required_dirs = [
        "app",
        "app/models",
        "app/routes",
        "migrations"
    ]
    
    required_files = [
        "app/__init__.py",
        "app/config.py",
        "app/extensions.py",
        "app/models/__init__.py",
        "app/models/user.py",
        "app/models/product.py",
        "app/models/sale.py",
        "app/models/sale_item.py",
        "app/routes/__init__.py",
        "app/routes/auth.py",
        "app/routes/health.py",
        "app/routes/product.py",
        "app/routes/sale.py",
        "requirements.txt",
        "run.py",
        ".env"
    ]
    
    all_ok = True
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"❌ Diretório ausente: {dir_path}")
            all_ok = False
        else:
            print(f"✅ Diretório: {dir_path}")
    
    for file_path in required_files:
        if not check_file_exists(file_path):
            print(f"❌ Arquivo ausente: {file_path}")
            all_ok = False
        else:
            print(f"✅ Arquivo: {file_path}")
    
    return all_ok

def check_python_modules():
    """Verifica módulos Python instalados"""
    print("\n🐍 Verificando módulos Python...")
    
    required_modules = [
        "flask",
        "flask_sqlalchemy",
        "flask_jwt_extended",
        "flask_bcrypt",
        "flask_migrate",
        "psycopg2",
        "python_dotenv"
    ]
    
    all_ok = True
    
    for module in required_modules:
        try:
            __import__(module.replace('_', ''))
            print(f"✅ Módulo: {module}")
        except ImportError:
            print(f"❌ Módulo ausente: {module}")
            all_ok = False
    
    return all_ok

def check_database_connection():
    """Verifica conexão com banco de dados"""
    print("\n🗄️  Verificando banco de dados...")
    
    # Lê configuração do .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        db_url = os.getenv("DATABASE_URL", "")
        
        if not db_url:
            print("❌ DATABASE_URL não definido no .env")
            return False
        
        print(f"✅ DATABASE_URL configurado")
        print(f"   URL: {db_url.split('@')[-1] if '@' in db_url else db_url}")
        
        # Tenta importar e conectar
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            # Extrai informações da URL
            parsed = urlparse(db_url)
            
            conn_info = {
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path[1:],
                'user': parsed.username,
                'password': parsed.password
            }
            
            print(f"   Tentando conectar...")
            conn = psycopg2.connect(**conn_info)
            conn.close()
            print(f"✅ Conexão com PostgreSQL bem-sucedida!")
            return True
            
        except psycopg2.OperationalError as e:
            print(f"❌ Falha na conexão: {str(e)}")
            print(f"\n🔧 Solução:")
            print(f"   1. Verifique se PostgreSQL está rodando")
            print(f"   2. Crie o banco: CREATE DATABASE gestormei;")
            print(f"   3. Atualize o .env com credenciais corretas")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {str(e)}")
        return False

def check_flask_app():
    """Verifica se a aplicação Flask pode ser importada"""
    print("\n🚀 Verificando aplicação Flask...")
    
    try:
        # Adiciona diretório atual ao path
        sys.path.insert(0, os.getcwd())
        
        from app import create_app
        
        print("✅ Aplicação Flask pode ser importada")
        
        # Tenta criar a app
        try:
            app = create_app("development")
            print("✅ Aplicação Flask criada com sucesso")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar aplicação: {str(e)}")
            return False
            
    except ImportError as e:
        print(f"❌ Erro ao importar: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False

def run_simple_test():
    """Executa teste simples"""
    print("\n🧪 Executando teste simples...")
    
    try:
        import requests
        
        try:
            response = requests.get("http://localhost:5000/", timeout=2)
            print(f"✅ Página inicial responde (status {response.status_code})")
            return True
        except requests.exceptions.ConnectionError:
            print("❌ Servidor não está rodando")
            print(f"\n🚀 Execute o servidor em outro terminal:")
            print(f"   python run.py")
            return False
            
    except ImportError:
        print("❌ requests não instalado. Execute:")
        print("   pip install requests")
        return False

def main():
    """Função principal"""
    
    print("="*60)
    print("🔧 DEBUG DO GESTORMEI API")
    print("="*60)
    
    steps = [
        ("Estrutura de diretórios", check_directory_structure),
        ("Módulos Python", check_python_modules),
        ("Aplicação Flask", check_flask_app),
        ("Banco de dados", check_database_connection),
        ("Teste simples", run_simple_test)
    ]
    
    results = []
    
    for step_name, step_func in steps:
        print(f"\n{'='*40}")
        print(f"Passo: {step_name}")
        print(f"{'='*40}")
        try:
            success = step_func()
            results.append((step_name, success))
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            results.append((step_name, False))
    
    # Resumo
    print(f"\n{'='*60}")
    print("📊 RESUMO DO DEBUG")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for step_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")
    
    print(f"\nTotal: {passed}/{total} passaram")
    
    if passed < total:
        print(f"\n🔧 PROBLEMAS ENCONTRADOS:")
        for step_name, success in results:
            if not success:
                print(f"   - {step_name}")
        
        print(f"\n🚀 SOLUÇÕES SUGERIDAS:")
        print(f"   1. Execute setup.py: python setup.py")
        print(f"   2. Instale dependências: pip install -r requirements.txt")
        print(f"   3. Configure o .env com DATABASE_URL correta")
        print(f"   4. Execute init_db.py: python init_db.py")
        print(f"   5. Inicie o servidor: python run.py")
    else:
        print(f"\n🎉 Tudo OK! O servidor deve funcionar corretamente.")
        print(f"\n🚀 Para iniciar: python run.py")
        print(f"🌐 Acesse: http://localhost:5000")

if __name__ == "__main__":
    main()