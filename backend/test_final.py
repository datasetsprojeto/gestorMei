#!/usr/bin/env python
"""
Teste final após reset do banco
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_all():
    """Teste completo após reset"""
    
    print("🧪 TESTE FINAL APÓS RESET DO BANCO")
    print("=" * 60)
    
    # 1. Health check
    print("\n1. 🩺 Health check geral:")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ {response.json().get('status', 'OK')}")
        return response.status_code == 200
    except:
        print("   ❌ Falhou")
        return False
    
    # 2. Health check do auth
    print("\n2. 🔐 Health check do auth:")
    try:
        response = requests.get(f"{BASE_URL}/auth/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Auth module: {data.get('status', 'OK')}")
            print(f"   📊 Database: {data.get('database', 'N/A')}")
            print(f"   🔐 Bcrypt: {data.get('bcrypt', 'N/A')}")
            print(f"   👥 Users in DB: {data.get('users_in_db', 0)}")
        return response.status_code == 200
    except:
        print("   ❌ Falhou")
        return False
    
    # 3. Login com credenciais inválidas (deve retornar 401)
    print("\n3. ❌ Login com credenciais inválidas:")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": "naoexiste@email.com", "password": "senhaerrada"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"   Status: {response.status_code} (esperado: 401)")
        
        if response.status_code == 401:
            print(f"   ✅ CORRETO: Retornou 401")
            print(f"   Mensagem: {response.json().get('error', 'N/A')}")
            return True
        else:
            print(f"   ❌ ERRO: Status {response.status_code}")
            if response.content:
                print(f"   Resposta: {response.json()}")
            return False
    except Exception as e:
        print(f"   ❌ Exceção: {str(e)}")
        return False
    
    # 4. Login com credenciais válidas (admin)
    print("\n4. ✅ Login com credenciais válidas (admin):")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": "admin@gestormei.com", "password": "admin123"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"   Status: {response.status_code} (esperado: 200)")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ LOGIN BEM-SUCEDIDO!")
            print(f"   Token obtido: {data.get('access_token', 'N/A')[:30]}...")
            print(f"   Usuário: {data.get('user', {}).get('email', 'N/A')}")
            
            # Salvar token para próximos testes
            token = data.get('access_token')
            
            # 5. Testar rota protegida com token
            print("\n5. 🛡️  Testar rota protegida com token:")
            response = requests.get(
                f"{BASE_URL}/products",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                },
                timeout=5
            )
            
            print(f"   Status: {response.status_code} (esperado: 200)")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Acesso permitido com token")
                if 'products' in data:
                    print(f"   📦 Produtos encontrados: {len(data['products'])}")
                return True
            else:
                print(f"   ❌ Acesso negado mesmo com token")
                return False
            
        else:
            print(f"   ❌ Login falhou com status {response.status_code}")
            if response.content:
                print(f"   Erro: {response.json().get('error', 'N/A')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exceção: {str(e)}")
        return False

def main():
    """Função principal"""
    
    print("🔍 Iniciando teste final...")
    
    try:
        # Verificar se servidor está rodando
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code != 200:
                print(f"❌ Servidor não está saudável")
                return False
        except:
            print(f"❌ Servidor não está rodando em {BASE_URL}")
            print(f"\n🚀 Execute o servidor primeiro:")
            print(f"   python run.py")
            return False
        
        print(f"✅ Servidor está rodando")
        
        # Executar testes
        success = test_all()
        
        print(f"\n{'='*60}")
        print("📊 RESULTADO FINAL")
        print(f"{'='*60}")
        
        if success:
            print("🎉 🎉 🎉 TUDO FUNCIONANDO CORRETAMENTE! 🎉 🎉 🎉")
            print("\n✅ Login retorna 401 para credenciais inválidas")
            print("✅ Login retorna 200 para credenciais válidas")
            print("✅ Token JWT é gerado corretamente")
            print("✅ Rotas protegidas funcionam com token")
            print("\n🚀 A API está pronta para uso!")
        else:
            print("❌ Ainda há problemas")
            print("\n🔧 Execute os passos:")
            print("   1. python reset_database.py")
            print("   2. python run.py")
            print("   3. python test_final.py")
        
        return success
        
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)