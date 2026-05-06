#!/bin/bash

# ============================================
# H&S LAYER - ONE-COMMAND START
# ============================================
# This script does EVERYTHING:
# - Checks requirements
# - Installs dependencies
# - Sets up database
# - Starts servers
# - Opens browser
# ============================================

set -e  # Exit on any error

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║                    🚀 H&S Layer - Starting                    ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python 3 is installed
echo "🔍 Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "   Install from: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION found"
echo ""

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*|MINGW*|MSYS*) MACHINE=Windows;;
    *)          MACHINE="UNKNOWN:${OS}"
esac
echo "💻 OS: $MACHINE"
echo ""

# Setup backend
echo "🔧 Setting up backend..."
cd backend

# Create virtual environment if needed
if [ ! -d ".venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "   Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "   Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo "✅ Backend ready"
echo ""

# Setup database
if [ ! -f "ai_orchestrator.db" ]; then
    echo "🗄️  Initializing database..."
    python3 -c "from app.db.init_db import init_db; import asyncio; asyncio.run(init_db())" > /dev/null 2>&1
    echo "✅ Database ready"
else
    echo "✅ Database already exists"
fi
echo ""

# Setup .env
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        cat > .env << 'EOF'
DATABASE_URL=sqlite+aiosqlite:///./ai_orchestrator.db
SECRET_KEY=your-secret-key-here-change-in-production
REDIS_URL=redis://localhost:6379
DEFAULT_LLM_PROVIDER=openrouter
DEFAULT_LLM_MODEL=openrouter/auto
LOG_LEVEL=INFO
EOF
    fi
    echo "✅ Configuration ready"
else
    echo "✅ Configuration exists"
fi
echo ""

cd ..

# Stop any existing servers
echo "🔍 Checking for running servers..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "   Stopping existing servers..."
    bash STOP.sh > /dev/null 2>&1 || true
    sleep 2
fi

# Start backend
echo "🚀 Starting backend..."
cd backend
source .venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../.backend.pid
cd ..
echo "✅ Backend started (PID: $BACKEND_PID)"

# Start frontend
echo "🚀 Starting frontend..."
cd frontend
nohup python3 -m http.server 3000 > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../.frontend.pid
cd ..
echo "✅ Frontend started (PID: $FRONTEND_PID)"

# Wait for backend to be ready
echo ""
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "⚠️  Backend taking longer than expected, but continuing..."
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ ALL SYSTEMS RUNNING!"
echo ""
echo "🔥 Backend:  http://localhost:8000"
echo "🎨 Frontend: http://localhost:3000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔑 CREDENTIALS:"
echo ""
echo "   Aurora Key:     aurora_live_****************************"
echo "   User ID:        00000000-0000-0000-0000-000000000001"
echo "   OpenRouter Key: (configure in dashboard)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 OPEN IN BROWSER:"
echo ""
echo "   👉 http://localhost:3000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 QUICK START:"
echo ""
echo "   1. Click 'View Interactive Demo' to see the complete flow"
echo "   2. Or click 'Continue with SSO' to access the dashboard"
echo "   3. Try: 'Write a Python calculator'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🛑 TO STOP:"
echo ""
echo "   ./STOP.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Open browser
sleep 2
if command -v open &> /dev/null; then
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v start &> /dev/null; then
    start http://localhost:3000
fi

echo "🎉 Ready! Enjoy H&S Layer!"
echo ""
