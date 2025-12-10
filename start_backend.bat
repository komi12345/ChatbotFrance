@echo off
echo ========================================
echo   Demarrage du Backend FastAPI
echo ========================================
echo.

cd backend

echo Installation des dependances...
pip install -r requirements.txt -q

echo.
echo Demarrage du serveur sur http://localhost:8000
echo Documentation API: http://localhost:8000/api/docs
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
