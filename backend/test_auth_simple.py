#!/usr/bin/env python
"""
Teste simplificado para auth.py - Focado no erro do login
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_login_error():
    """Teste específico para o erro do login"""
    
    print("🧪 TESTE ESPECÍFICO - ERRO DE LOGIN")
    print("=" * 60)
    
    # Caso 1: Login com credenciais inválidas (deve retornar 401)
    print("\n1. Login com credenciais inválidas (deve retornar 401):")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "naoexiste@email.com", "password": "senhaerrada"},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response.status_code}")
    print(f"   Resposta: {response.json() if response.content else 'Sem conteúdo'}")
    
    if response.status_code == 401:
        print("   ✅ CORRETO: Retornou 401 para credenciais inválidas")
        return True
    else:
        print(f"   ❌ ERRO: Esperado 401, recebido {response.status_code}")
        
        # Mostrar mais detalhes do erro
        if response.status_code == 500:
            print("\n   🔍 Detalhes do erro 500:")
            try:
                error_data = response.json()
                print(f"      Erro: {error_data.get('error', 'N/A')}")
            except:
                print(f"      Resposta bruta: {response.text[:200]}")
        
        return False

def test_registration():
    """Teste de registro para criar um usuário de teste"""
    
    print("\n2. Teste de registro (para depois testar login):")
    
    # Email único
    import random
    import string
    random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
    test_email = f"teste_{random_str}@email.com"
    
    user_data = {
        "name": "Usuário Teste",
        "email": test_email,
        "password": "senha123"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=user_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 201:
        print(f"   ✅ Usuário registrado: {test_email}")
        return test_email, "senha123"
    elif response.status_code == 500:
        print(f"   ❌ Erro 500 no registro")
        error_data = response.json()
        print(f"      Erro: {error_data.get('error', 'N/A')}")
        return None, None
    else:
        print(f"   ❌ Status inesperado: {response.status_code}")
        return None, None

def test_login_success(email, password):
    """Teste de login com credenciais válidas"""
    
    if not email:
        return False
    
    print(f"\n3. Teste de login válido com {email}:")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Login bem-sucedido!")
        print(f"      Token: {data.get('access_token', 'N/A')[:30]}...")
        print(f"      Usuário ID: {data.get('user', {}).get('id', 'N/A')}")
        return True
    else:
        print(f"   ❌ Login falhou com status {response.status_code}")
        if response.content:
            print(f"      Erro: {response.json().get('error', 'N/A')}")
        return False

def test_auth_endpoints():
    """Testa todos os endpoints de auth"""
    
    print("\n4. Testando todos os endpoints de auth:")
    
    endpoints = [
        ("GET", "/auth/test", None, 200, False),
        ("GET", "/auth/health", None, 200, False),
        ("GET", "/auth/verify", None, 200, False),
    ]
    
    for method, endpoint, data, expected_status, auth_required in endpoints:
        print(f"\n   {method} {endpoint}:")
        
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=5)
            
            print(f"      Status: {response.status_code} (esperado: {expected_status})")
            
            if response.status_code == expected_status:
                print("      ✅ OK")
            else:
                print(f"      ❌ Status inesperado")
                if response.content:
                    print(f"         Resposta: {response.json()}")
                    
        except Exception as e:
            print(f"      ❌ Erro: {str(e)}")

def main():
    """Função principal"""
    
    print("🔍 Verificando servidor...")
    
    try:
        # Primeiro verifica se o servidor está rodando
        health_response = requests.get(f"{BASE_URL}/health", timeout=2)
        
        if health_response.status_code != 200:
            print(f"❌ Servidor não está saudável: {health_response.status_code}")
            return False
            
        print(f"✅ Servidor está rodando em {BASE_URL}")
        
        # Executar testes
        test_1_success = test_login_error()
        
        # Testar registro e login se o primeiro teste passar
        if test_1_success:
            test_email, test_password = test_registration()
            
            if test_email:
                test_login_success(test_email, test_password)
        
        # Testar outros endpoints
        test_auth_endpoints()
        
        print(f"\n{'='*60}")
        print("🧪 TESTES CONCLUÍDOS")
        print(f"{'='*60}")
        
        if test_1_success:
            print("✅ O problema do login foi resolvido!")
            print("\n📋 Próximos passos:")
            print("   1. Execute os testes completos novamente")
            print("   2. Teste com diferentes cenários")
        else:
            print("❌ Ainda há problemas com o login")
            print("\n🔧 Verifique:")
            print("   1. Logs do servidor Flask")
            print("   2. Conexão com banco de dados")
            print("   3. Configuração do bcrypt/JWT")
        
        return test_1_success
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Não foi possível conectar ao servidor em {BASE_URL}")
        print(f"\n🚀 Execute o servidor primeiro:")
        print(f"   python run.py")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)