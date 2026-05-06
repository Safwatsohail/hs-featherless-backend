#!/bin/bash

# ============================================
# H&S LAYER - STOP SERVERS
# ============================================

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║                    🛑 H&S Layer - Stopping                    ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Stop backend
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "🛑 Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    rm .backend.pid
    echo "✅ Backend stopped"
else
    echo "⚠️  No backend PID file found"
fi

# Stop frontend
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    echo "🛑 Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
    rm .frontend.pid
    echo "✅ Frontend stopped"
else
    echo "⚠️  No frontend PID file found"
fi

echo ""
echo "🔍 Checking for any remaining processes..."

# Kill any process on port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    PIDS=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    echo "🛑 Killing process on port 8000 (PID: $PIDS)..."
    kill -9 $PIDS 2>/dev/null || true
fi

# Kill any process on port 3000
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    PIDS=$(lsof -Pi :3000 -sTCP:LISTEN -t)
    echo "🛑 Killing process on port 3000 (PID: $PIDS)..."
    kill -9 $PIDS 2>/dev/null || true
fi

echo ""
echo "✅ All servers stopped!"
echo ""
echo "💡 To start again: ./START.sh"
echo ""
