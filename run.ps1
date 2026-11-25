# AI Sales Voice Agent Startup Script
# This script starts both the backend and frontend

Write-Host "================================" -ForegroundColor Cyan
Write-Host "🤖 AI Sales Voice Agent Startup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install/update dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -q

# Check if .env file exists
if (-Not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "⚠️  .env file not found!" -ForegroundColor Red
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "Please edit .env and add your Gemini API key:" -ForegroundColor Yellow
    Write-Host "GEMINI_API_KEY=your_actual_api_key_here" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter after updating .env to continue"
}

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
python -c "from backend.app.database import init_db; init_db(); print('Database initialized!')" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✅ Startup Complete" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host ""

Write-Host "📌 Backend will run on: http://localhost:8000" -ForegroundColor Green
Write-Host "📌 Frontend will run on: http://localhost:8501" -ForegroundColor Green
Write-Host "📌 API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""

Write-Host "Starting Backend Server (Press Ctrl+C to stop)..." -ForegroundColor Yellow
Write-Host ""

# Start backend in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; & '.\venv\Scripts\Activate.ps1'; cd backend; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend
Write-Host ""
Write-Host "Starting Frontend (Streamlit will open in browser)..." -ForegroundColor Yellow
Write-Host ""

cd frontend
streamlit run app.py
