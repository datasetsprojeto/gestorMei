@echo off
setlocal
chcp 65001 >nul

set "ROOT=%~dp0"
set "VENV_PY=%ROOT%.venv\Scripts\python.exe"
set "SYS_PY=C:\Python313\python.exe"

echo Iniciando GestorMEI...

echo [1/2] Subindo backend na porta 5000...
if exist "%VENV_PY%" (
	start "GestorMEI Backend" cmd /k "cd /d ""%ROOT%backend"" && "%VENV_PY%" run.py"
) else if exist "%SYS_PY%" (
	start "GestorMEI Backend" cmd /k "cd /d ""%ROOT%backend"" && "%SYS_PY%" run.py"
) else (
	start "GestorMEI Backend" cmd /k "cd /d ""%ROOT%backend"" && python run.py"
)

timeout /t 4 >nul

echo [2/2] Subindo frontend na porta 5501...
if exist "%VENV_PY%" (
	start "GestorMEI Frontend" cmd /k "cd /d ""%ROOT%frontend"" && "%VENV_PY%" -m http.server 5501"
) else if exist "%SYS_PY%" (
	start "GestorMEI Frontend" cmd /k "cd /d ""%ROOT%frontend"" && "%SYS_PY%" -m http.server 5501"
) else (
	start "GestorMEI Frontend" cmd /k "cd /d ""%ROOT%frontend"" && python -m http.server 5501"
)

timeout /t 2 >nul
start "" "http://localhost:5501/index.html"

echo Pronto. Backend: http://localhost:5000 ^| Frontend: http://localhost:5501/index.html
endlocal
