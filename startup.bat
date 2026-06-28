@echo off
REM FYP Startup Script for Windows
REM Starts all three services: Database, Backend, Frontend in separate windows

setlocal enabledelayedexpansion

echo.
echo ===============================================================
echo   AI-Driven Pose Estimation Application Startup
echo ===============================================================
echo.

REM Check if Docker Desktop is running
echo 🐳 Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please open Docker Desktop and try again.
    pause
    exit /b 1
)
echo ✓ Docker is running
echo.

REM Start PostgreSQL container
echo 🗄️  Starting PostgreSQL container...
docker compose up -d
if errorlevel 1 (
    echo ❌ Failed to start Docker container. Check docker-compose.yml
    pause
    exit /b 1
)
echo ✓ PostgreSQL started (background)
timeout /t 2 /nobreak >nul
echo.

REM Start Backend in a new window
echo 🔧 Starting Backend API on http://localhost:8000...
cd backend
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found. Run the First Time Setup in README.md
    pause
    exit /b 1
)
start "FYP Backend" cmd /k ".venv\Scripts\activate && uvicorn app.main:app --reload"
cd ..
timeout /t 3 /nobreak >nul
echo ✓ Backend started
echo.

REM Start Frontend in a new window
echo ⚛️  Starting Frontend on http://localhost:5173...
cd frontend
start "FYP Frontend" cmd /k "npm run dev"
cd ..
timeout /t 3 /nobreak >nul
echo ✓ Frontend started
echo.

echo ===============================================================
echo   ✅ All services started!
echo ===============================================================
echo.
echo 📱 Open your browser:
echo    → http://localhost:5173 (React Frontend)
echo.
echo 📚 API Documentation:
echo    → http://localhost:8000/docs (Swagger UI)
echo.
echo ⚠️  To stop services:
echo    - Close the Backend and Frontend windows (Ctrl+C)
echo    - Run: docker compose down (to stop database)
echo.
pause
