@echo off
echo Lancement du Serveur Backend (FastAPI)...
title Serveur MediaFlow
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
pause
