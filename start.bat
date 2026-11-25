@echo off
REM AI Sales Voice Agent - Windows Batch Startup Script
REM This avoids PowerShell alias issues

setlocal enabledelayedexpansion

set PYTHON_PATH=C:\Users\solos\AppData\Local\Python\pythoncore-3.12-64\python.exe
set PROJECT_ROOT=%~dp0

REM Check if Python exists
if not exist "%PYTHON_PATH%" (
    echo.
    echo ❌ Python not found at: %PYTHON_PATH%
    echo.
    echo Please install Python 3.12 first:
    echo https://www.python.org/downloads/windows/
    echo.
    pause
    exit /b 1
)

cls
echo.
echo ════════════════════════════════════════════════════════════
echo.    AI Sales Voice Agent - Startup
echo.
echo ════════════════════════════════════════════════════════════
echo.

REM Create venv if it doesn't exist
if not exist "%PROJECT_ROOT%venv" (
    echo Creating Python virtual environment...
    "%PYTHON_PATH%" -m venv "%PROJECT_ROOT%venv"
    echo - Virtual environment created
    echo.
)

REM Activate venv
echo Activating virtual environment...
call "%PROJECT_ROOT%venv\Scripts\activate.bat"

REM Install dependencies if needed
echo Checking dependencies...
"%PYTHON_PATH%" -c "import fastapi, streamlit, sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies ^(first time: 2-3 minutes^)...
    call pip install -r "%PROJECT_ROOT%requirements.txt" -q
    echo - Dependencies installed
    echo.
)

REM Check .env file
if not exist "%PROJECT_ROOT%.env" (
    echo.
    echo WARNING: .env file not found!
    echo Creating from template...
    copy "%PROJECT_ROOT%.env.example" "%PROJECT_ROOT%.env" >nul
    echo.
    echo IMPORTANT: Add your Gemini API key
    echo.
    echo 1. Go to: https://makersuite.google.com/app/apikey
    echo 2. Create an API key
    echo 3. Edit .env file:
    echo    notepad %PROJECT_ROOT%.env
    echo 4. Find: GEMINI_API_KEY=your_gemini_api_key_here
    echo 5. Replace with your actual key
    echo 6. Save and close
    echo.
    pause
)

REM Initialize database
echo Initializing database...
"%PYTHON_PATH%" -c "from backend.app.database import init_db; init_db()" >nul 2>&1

cls
echo.
echo ════════════════════════════════════════════════════════════
echo.    Setup Complete! Starting services...
echo.
echo ════════════════════════════════════════════════════════════
echo.

echo Dashboard:    http://localhost:8501
echo API Server:   http://localhost:8000
echo Documentation: http://localhost:8000/docs
echo.

echo Starting Backend Server...
echo.

REM Start backend in new window
start "AI Sales Voice Agent - Backend" cmd /k "title Backend Server && cd /d %PROJECT_ROOT%backend && %PROJECT_ROOT%venv\Scripts\activate.bat && %PYTHON_PATH% -m uvicorn app.main:app --reload"

REM Wait for backend to start
timeout /t 4 /nobreak >nul

REM Start frontend
echo Starting Frontend Dashboard...
echo.

cd /d "%PROJECT_ROOT%frontend"
call %PROJECT_ROOT%venv\Scripts\activate.bat
%PYTHON_PATH% -m streamlit run app.py --logger.level=error
