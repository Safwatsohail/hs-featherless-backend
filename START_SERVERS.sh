#!/bin/bash

# Enhanced AI API - Start Both Servers
# This script starts the backend and frontend servers

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                    🚀 Starting Enhanced AI API Servers                       ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if backend is already running
if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "✅ Backend already running on port 8000"
else
    echo "🔄 Starting backend on port 8000..."
    cd backend
    source .venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../.backend.pid
    cd ..
    sleep 3
    
    if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
        echo "✅ Backend started successfully (PID: $BACKEND_PID)"
    else
        echo "❌ Backend failed to start. Check backend.log"
        exit 1
    fi
fi

# Check if frontend is already running
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend already running on port 3000"
else
    echo "🔄 Starting frontend on port 3000..."
    cd frontend
    nohup python3 -m http.server 3000 > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../.frontend.pid
    cd ..
    sleep 2
    
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend started successfully (PID: $FRONTEND_PID)"
    else
        echo "❌ Frontend failed to start. Check frontend.log"
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ BOTH SERVERS RUNNING!"
echo ""
echo "🔥 Backend:  http://localhost:8000"
echo "🎨 Frontend: http://localhost:3000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔑 YOUR CREDENTIALS:"
echo ""
echo "   Aurora Key:     aurora_live_6BYZvwXhx0qmmifrwTYtUnRpLydoeSGy"
echo "   User ID:        00000000-0000-0000-0000-000000000001"
echo "   OpenRouter Key: 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"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 OPEN IN BROWSER:"
echo ""
echo "   👉 http://localhost:3000#dashboard"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 QUICK TEST:"
echo ""
echo "   1. Open: http://localhost:3000#dashboard"
echo "   2. Click: 'A/B Chat' tab"
echo "   3. Type: 'What is 2+2?'"
echo "   4. Click: 'Run Comparison'"
echo "   5. Watch: Real-time responses!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 To stop servers: ./STOP_SERVERS.sh"
echo "📊 View logs: tail -f backend.log frontend.log"
echo ""
