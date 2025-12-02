#!/bin/bash

# Simple startup script
echo "🚀 Starting Personal Finance Insight Engine..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q fastapi uvicorn[standard] psycopg2-binary python-dotenv pandas numpy pyodbc pydantic

# Start backend
echo "🔧 Starting Backend API..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a bit
sleep 3

# Start frontend
echo "🌐 Starting Frontend..."
cd frontend
python -m http.server 8080 &
FRONTEND_PID=$!
cd ..

# Wait a bit
sleep 2

echo ""
echo "=========================================="
echo "✅ Application Started!"
echo "=========================================="
echo ""
echo "📍 Access Points:"
echo "   • Frontend: http://localhost:8080"
echo "   • Backend:  http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Keep script running
wait

