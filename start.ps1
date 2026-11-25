# AI Sales Voice Agent - Quick Start Script
# This script bypasses the Windows Python alias issue

$pythonExe = "C:\Users\solos\AppData\Local\Python\pythoncore-3.12-64\python.exe"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "================================" -ForegroundColor Cyan
Write-Host "🤖 AI Sales Voice Agent Startup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (-Not (Test-Path "$projectRoot\venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    & $pythonExe -m venv "$projectRoot\venv"
    Write-Host "Virtual environment created!" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "$projectRoot\venv\Scripts\Activate.ps1"

# Check if packages are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$packagesOk = & $pythonExe -c "import fastapi, streamlit, sqlalchemy; print('OK')" 2>&1
if ($packagesOk -notcontains "OK") {
    Write-Host "Installing dependencies (this takes 2-3 minutes)..." -ForegroundColor Yellow
    & pip install -r "$projectRoot\requirements.txt" -q
    Write-Host "Dependencies installed!" -ForegroundColor Green
}

# Check if .env exists
if (-Not (Test-Path "$projectRoot\.env")) {
    Write-Host ""
    Write-Host "⚠️  .env file not found!" -ForegroundColor Red
    Write-Host "Creating from template..." -ForegroundColor Yellow
    Copy-Item "$projectRoot\.env.example" "$projectRoot\.env"
    Write-Host ""
    Write-Host "📋 You need to add your Gemini API key:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://makersuite.google.com/app/apikey" -ForegroundColor Cyan
    Write-Host "2. Create an API key" -ForegroundColor Cyan
    Write-Host "3. Edit .env file:" -ForegroundColor Yellow
    Write-Host "   notepad $projectRoot\.env" -ForegroundColor Gray
    Write-Host "4. Find: GEMINI_API_KEY=your_gemini_api_key_here" -ForegroundColor Gray
    Write-Host "5. Replace with your actual key" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter after adding your API key"
}

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
& $pythonExe -c "from backend.app.database import init_db; init_db()" 2>&1 | Out-Null

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host ""
Write-Host "📌 Frontend: http://localhost:8501" -ForegroundColor Green
Write-Host "📌 Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "📌 API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""

Write-Host "Starting Backend (press Ctrl+C to stop)..." -ForegroundColor Yellow
Write-Host ""

# Start backend in new window
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; & '$projectRoot\venv\Scripts\Activate.ps1'; cd backend; $pythonExe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -PassThru

# Wait for backend to start
Start-Sleep -Seconds 3

# Start frontend
Write-Host ""
Write-Host "Starting Frontend..." -ForegroundColor Yellow
Write-Host ""

cd "$projectRoot\frontend"
& $pythonExe -m streamlit run app.py
