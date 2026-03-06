#!/bin/bash

# Ativar ambiente virtual
source venv/bin/activate

# Definir ambiente
export FLASK_ENV=development
export FLASK_APP=run.py

# Iniciar servidor
echo "🚀 Iniciando GestorMEI API..."
echo "📁 Diretório: $(pwd)"
echo "🌐 Acesse: http://localhost:5000"
echo ""

python run.py