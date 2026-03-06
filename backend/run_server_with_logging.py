#!/usr/bin/env python
"""
Script para rodar o servidor com logging detalhado
"""

import os
import sys
import logging
from app import create_app

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('server.log')
    ]
)

# Criar app
app = create_app("development")

# Configurar logging do Flask
app.logger.setLevel(logging.DEBUG)

# Log de todas as requisições
@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', dict(request.headers))
    app.logger.debug('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    app.logger.debug('Status: %s', response.status)
    app.logger.debug('Headers: %s', dict(response.headers))
    return response

if __name__ == "__main__":
    print("🚀 Iniciando servidor com logging detalhado...")
    print("📝 Logs serão salvos em server.log")
    print("🔍 Nível de log: DEBUG")
    print(f"🌐 Servidor rodando em: http://localhost:5000")
    print("-" * 50)
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=True
    )