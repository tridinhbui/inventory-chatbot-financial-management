#!/usr/bin/env python3
"""
Personal Finance Insight Engine - Run Script (Python version)
Starts backend API and frontend server
"""

import os
import sys
import subprocess
import time
import signal
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import psycopg2
        import pandas
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True

def start_backend():
    """Start FastAPI backend server"""
    print("🚀 Starting Backend API...")
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Start uvicorn server
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait a bit for server to start
    time.sleep(3)
    
    # Check if process is still running
    if process.poll() is None:
        print("✅ Backend API started on http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        return process
    else:
        stdout, stderr = process.communicate()
        print(f"❌ Backend failed to start:")
        print(stderr.decode())
        return None

def start_frontend():
    """Start frontend HTTP server"""
    print("🌐 Starting Frontend Server...")
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    # Start HTTP server
    process = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8080"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(2)
    
    if process.poll() is None:
        print("✅ Frontend server started on http://localhost:8080")
        return process
    else:
        stdout, stderr = process.communicate()
        print(f"❌ Frontend failed to start:")
        print(stderr.decode())
        return None

def main():
    """Main function to run the application"""
    print("=" * 60)
    print("💰 Personal Finance Insight Engine v2.0")
    print("=" * 60)
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Please install dependencies first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Change to project root
    os.chdir(Path(__file__).parent)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✅ Application Started Successfully!")
    print("=" * 60)
    print()
    print("📍 Access Points:")
    print("   • Frontend Dashboard: http://localhost:8080")
    print("   • Backend API: http://localhost:8000")
    print("   • API Documentation: http://localhost:8000/docs")
    print("   • Health Check: http://localhost:8000/health")
    print()
    print("💡 Tips:")
    print("   • Use User ID: 1 (if you have sample data)")
    print("   • Check API docs for all available endpoints")
    print("   • Press Ctrl+C to stop all services")
    print()
    
    # Open browser (optional)
    try:
        time.sleep(2)
        webbrowser.open("http://localhost:8080")
    except:
        pass
    
    # Wait for interrupt
    try:
        while True:
            time.sleep(1)
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped unexpectedly")
                break
    except KeyboardInterrupt:
        print()
        print("🛑 Stopping services...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Services stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()

