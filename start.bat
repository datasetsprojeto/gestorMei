@echo off
setlocal
chcp 65001 >nul

set "ROOT=%~dp0"

echo Iniciando GestorMEI...

echo [1/2] Subindo backend na porta 5000...
start "GestorMEI Backend" cmd /k "cd /d "%ROOT%backend" && if exist "..\.venv\Scripts\python.exe" ("..\.venv\Scripts\python.exe" run.py) else (python run.py)"

timeout /t 4 >nul

echo [2/2] Subindo frontend na porta 5501...
start "GestorMEI Frontend" cmd /k "cd /d "%ROOT%frontend" && if exist "..\.venv\Scripts\python.exe" ("..\.venv\Scripts\python.exe" -m http.server 5501) else (python -m http.server 5501)"

timeout /t 2 >nul
start "" "http://localhost:5501/index.html"

echo Pronto. Backend: http://localhost:5000 | Frontend: http://localhost:5501/index.html
endlocal
