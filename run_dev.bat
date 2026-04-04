@echo off
echo ============================================
echo   MediaFlow — Mode developpement
echo ============================================
echo.

REM Activate venv if present
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python main.py
pause
