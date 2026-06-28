#!/bin/bash

# FYP Startup Script for macOS/Linux
# Starts all three services: Database, Backend, Frontend

set -e  # Exit on any error

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "═══════════════════════════════════════════════════════════"
echo "  AI-Driven Pose Estimation Application Startup"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if Docker is running
echo "🐳 Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please open Docker Desktop and try again."
    exit 1
fi
echo "✓ Docker is running"
echo ""

# Start PostgreSQL container
echo "🗄️  Starting PostgreSQL container..."
docker compose up -d
echo "✓ PostgreSQL started (background)"
sleep 2
echo ""

# Start Backend
echo "🔧 Starting Backend API on http://localhost:8000..."
cd backend
source .venv/bin/activate 2>/dev/null || {
    echo "❌ Virtual environment not found. Run the First Time Setup in README.md"
    exit 1
}
uvicorn app.main:app --reload > /tmp/fyp_backend.log 2>&1 &
BACKEND_PID=$!
sleep 3
echo "✓ Backend started (PID: $BACKEND_PID)"
echo ""

# Start Frontend
echo "⚛️  Starting Frontend on http://localhost:5173..."
cd ../frontend
npm run dev > /tmp/fyp_frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 3
echo "✓ Frontend started (PID: $FRONTEND_PID)"
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "  ✅ All services started!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📱 Open your browser:"
echo "   → http://localhost:5173 (React Frontend)"
echo ""
echo "📚 API Documentation:"
echo "   → http://localhost:8000/docs (Swagger UI)"
echo ""
echo "⚠️  To stop all services, press Ctrl+C or run:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   docker compose down"
echo ""
echo "📋 Logs:"
echo "   Backend:  tail -f /tmp/fyp_backend.log"
echo "   Frontend: tail -f /tmp/fyp_frontend.log"
echo ""

# Wait for user to stop the script
wait
