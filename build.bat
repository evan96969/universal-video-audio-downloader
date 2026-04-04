@echo off
echo ============================================
echo   Universal Downloader — Build Windows Executable
echo ============================================
echo.

REM Activate venv if present
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo [1/2] Nettoyage precedent...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo [2/2] Construction avec PyInstaller...
pyinstaller mediaflow.spec

echo.
if exist "dist\UniversalDownloader\UniversalDownloader.exe" (
    echo ============================================
    echo   Build reussi !
    echo   Executable : dist\UniversalDownloader\UniversalDownloader.exe
    echo ============================================
) else (
    echo ============================================
    echo   ERREUR : le build a echoue.
    echo ============================================
)

echo.
pause
