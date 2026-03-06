@echo off
chcp 65001 >nul

echo 🚀 Iniciando GestorMEI API...
echo 📁 Diret¢rio: %cd%
echo.

REM Ativar ambiente virtual
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ❌ Ambiente virtual n£o encontrado.
    echo Execute: python -m venv venv
    pause
    exit /b 1
)

REM Definir vari veis de ambiente
set FLASK_ENV=development
set FLASK_APP=run.py

REM Iniciar servidor
echo 🌐 Servidor rodando em: http://localhost:5000
echo 🔧 Modo debug: ATIVADO
echo.

python run.py

pause