@echo off
REM Construye SITRAFO.exe (aplicacion de escritorio en un solo archivo).
REM Requiere el entorno virtual .venv creado en esta carpeta.
cd /d "%~dp0"
.venv\Scripts\python.exe -m pip install --upgrade "pyinstaller>=6.11"
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name SITRAFO --icon sitrafo.ico --add-data "sitrafo.ico;." main.py
echo.
echo Listo: dist\SITRAFO.exe
pause
