#!/usr/bin/env python
"""
Script de setup para o GestorMEI API
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Executa um comando e mostra status"""
    print(f"\n📋 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Concluído")
            return True
        else:
            print(f"❌ {description} - Falhou")
            print(f"   Erro: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exceção: {str(e)}")
        return False

def main():
    """Função principal"""
    
    print("=" * 50)
    print("🚀 SETUP - GestorMEI API")
    print("=" * 50)
    
    # 1. Verificar Python
    if not run_command("python --version", "Verificando Python"):
        print("❌ Python não encontrado. Instale Python 3.8+ primeiro.")
        sys.exit(1)
    
    # 2. Criar ambiente virtual
    if not os.path.exists("venv"):
        if not run_command("python -m venv venv", "Criando ambiente virtual"):
            sys.exit(1)
    else:
        print("✅ Ambiente virtual já existe")
    
    # 3. Ativar ambiente virtual (depende do OS)
    print("\n📋 Ativando ambiente virtual...")
    if sys.platform == "win32":
        activate_script = "venv\\Scripts\\activate"
        pip_path = "venv\\Scripts\\pip"
        python_path = "venv\\Scripts\\python"
    else:
        activate_script = "venv/bin/activate"
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    print(f"   Execute: source {activate_script} (Linux/Mac)")
    print(f"   Execute: {activate_script} (Windows)")
    
    # 4. Instalar dependências
    print("\n📋 Instalando dependências...")
    if os.path.exists(pip_path):
        if not run_command(f'"{pip_path}" install -r requirements.txt', "Instalando pacotes"):
            print("   Tentando com pip normal...")
            run_command("pip install -r requirements.txt", "Instalando pacotes (fallback)")
    else:
        run_command("pip install -r requirements.txt", "Instalando pacotes")
    
    # 5. Criar arquivo .env
    if not os.path.exists(".env"):
        print("\n📋 Criando arquivo .env...")
        with open(".env.example", "r") as example_file:
            example_content = example_file.read()
        
        with open(".env", "w") as env_file:
            env_file.write(example_content)
        print("✅ Arquivo .env criado")
        print("   ⚠️  Edite o arquivo .env com suas configurações")
    else:
        print("✅ Arquivo .env já existe")
    
    # 6. Verificar PostgreSQL
    print("\n📋 Verificando PostgreSQL...")
    print("   Certifique-se de que:")
    print("   1. PostgreSQL está instalado e rodando")
    print("   2. O banco 'gestormei' existe")
    print("   3. As credenciais no .env estão corretas")
    
    # 7. Inicializar banco de dados
    print("\n📋 Inicializando banco de dados...")
    print("   Para criar o banco, execute:")
    print("   psql -U postgres -c \"CREATE DATABASE gestormei;\"")
    print("\n   Para inicializar com dados de exemplo, execute:")
    print("   python init_db.py")
    
    # 8. Executar migrações
    print("\n📋 Executando migrações...")
    print("   Execute os comandos:")
    print("   flask db init")
    print("   flask db migrate -m 'Initial migration'")
    print("   flask db upgrade")
    
    print("\n" + "=" * 50)
    print("🎉 SETUP COMPLETO!")
    print("=" * 50)
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Ative o ambiente virtual:")
    print("   - Windows: venv\\Scripts\\activate")
    print("   - Linux/Mac: source venv/bin/activate")
    print("\n2. Configure o PostgreSQL e edite o .env")
    print("\n3. Execute as migrações:")
    print("   flask db init")
    print("   flask db migrate -m 'Initial migration'")
    print("   flask db upgrade")
    print("\n4. Inicie o servidor:")
    print("   python run.py")
    print("\n5. Acesse: http://localhost:5000")
    print("\n💡 Dica: Use o script init_db.py para dados de exemplo")

if __name__ == "__main__":
    main()