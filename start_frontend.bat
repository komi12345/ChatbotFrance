@echo off
echo ========================================
echo   Demarrage du Frontend Next.js
echo ========================================
echo.

cd frontend

echo Installation des dependances...
npm install

echo.
echo Demarrage du serveur sur http://localhost:3000
echo.

npm run dev
