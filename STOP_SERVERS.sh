#!/bin/bash

# Enhanced AI API - Stop Both Servers

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                    🛑 Stopping Enhanced AI API Servers                       ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Stop backend
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "🛑 Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm .backend.pid
        echo "✅ Backend stopped"
    else
        echo "⚠️  Backend not running (stale PID file)"
        rm .backend.pid
    fi
else
    echo "⚠️  Backend PID file not found"
fi

# Stop frontend
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "🛑 Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm .frontend.pid
        echo "✅ Frontend stopped"
    else
        echo "⚠️  Frontend not running (stale PID file)"
        rm .frontend.pid
    fi
else
    echo "⚠️  Frontend PID file not found"
fi

# Also try to kill by port (backup method)
echo ""
echo "🔍 Checking for any remaining processes..."

# Kill any process on port 8000
BACKEND_PORT_PID=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$BACKEND_PORT_PID" ]; then
    echo "🛑 Killing process on port 8000 (PID: $BACKEND_PORT_PID)..."
    kill -9 $BACKEND_PORT_PID 2>/dev/null
fi

# Kill any process on port 3000
FRONTEND_PORT_PID=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$FRONTEND_PORT_PID" ]; then
    echo "🛑 Killing process on port 3000 (PID: $FRONTEND_PORT_PID)..."
    kill -9 $FRONTEND_PORT_PID 2>/dev/null
fi

echo ""
echo "✅ All servers stopped!"
echo ""
echo "💡 To start again: ./START_SERVERS.sh"
echo ""
