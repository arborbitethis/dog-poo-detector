#!/bin/bash

# Dog Poop Detector - Quick Start Script
# This is a simple alternative to start.py

set -e

echo "🐕 Dog Poop Detector - Development Server"
echo "=========================================="
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

trap cleanup EXIT INT TERM

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start backend in background
echo "Starting backend server (port 8080)..."
python3 demo.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start frontend in background
echo "Starting frontend dev server (port 5173)..."
cd frontend && npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

echo ""
echo "✓ All servers running!"
echo "=========================================="
echo ""
echo "🌐 Open your browser: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for processes
wait
