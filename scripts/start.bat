@echo off
cd /d "%~dp0\.."

if not exist .env (
    echo Error: .env file not found in project root
    exit /b 1
)

if not exist data mkdir data
docker compose up --build -d
echo PM App started at http://localhost:8000
