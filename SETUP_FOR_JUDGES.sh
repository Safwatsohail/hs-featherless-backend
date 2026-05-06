#!/bin/bash

# ============================================
# H&S LAYER - ONE-COMMAND SETUP FOR JUDGES
# ============================================
# This script sets up everything automatically
# No manual configuration needed!
# ============================================

set -e  # Exit on any error

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║           🚀 H&S Layer - Automated Setup for Judges          ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "This script will:"
echo "  ✓ Check system requirements"
echo "  ✓ Install Python dependencies"
echo "  ✓ Set up the database"
echo "  ✓ Configure API keys"
echo "  ✓ Start both servers"
echo "  ✓ Open the demo in your browser"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Python 3 is installed
echo "🔍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "   Please install Python 3.8+ from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Check if we're on macOS, Linux, or Windows
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*|MINGW*|MSYS*) MACHINE=Windows;;
    *)          MACHINE="UNKNOWN:${OS}"
esac
echo "💻 Detected OS: $MACHINE"
echo ""

# Create virtual environment if it doesn't exist
echo "🔧 Setting up Python virtual environment..."
cd backend
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo "✅ Dependencies installed"
echo ""

# Set up database
echo "🗄️  Setting up database..."
if [ ! -f "ai_orchestrator.db" ]; then
    python3 -c "from app.db.init_db import init_db; import asyncio; asyncio.run(init_db())" > /dev/null 2>&1
    echo "✅ Database initialized"
else
    echo "✅ Database already exists"
fi
echo ""

# Check if .env exists, if not create from example
echo "⚙️  Configuring environment..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from template"
    else
        echo "⚠️  No .env.example found, creating basic .env"
        cat > .env << 'EOF'
# H&S Layer Configuration
DATABASE_URL=sqlite+aiosqlite:///./ai_orchestrator.db
SECRET_KEY=your-secret-key-here-change-in-production
REDIS_URL=redis://localhost:6379
DEFAULT_LLM_PROVIDER=openrouter
DEFAULT_LLM_MODEL=openrouter/auto
LOG_LEVEL=INFO
EOF
    fi
else
    echo "✅ .env already configured"
fi
echo ""

cd ..

# Check if servers are already running
echo "🔍 Checking for running servers..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Backend already running on port 8000"
    echo "   Stopping existing server..."
    bash STOP_SERVERS.sh > /dev/null 2>&1 || true
    sleep 2
fi

# Start servers
echo "🚀 Starting servers..."
bash START_SERVERS.sh

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ SETUP COMPLETE!"
echo ""
echo "🎉 H&S Layer is now running!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 OPEN IN BROWSER:"
echo ""
echo "   👉 http://localhost:3000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 QUICK START:"
echo ""
echo "   1. Click 'View Interactive Demo' to see the complete flow"
echo "   2. Or click 'Continue with SSO' to access the dashboard"
echo "   3. Try the A/B comparison with: 'Write a Python calculator'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🛑 TO STOP SERVERS:"
echo ""
echo "   ./STOP_SERVERS.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Try to open browser automatically
sleep 3
if command -v open &> /dev/null; then
    # macOS
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open http://localhost:3000
elif command -v start &> /dev/null; then
    # Windows
    start http://localhost:3000
else
    echo "💡 Please open http://localhost:3000 in your browser"
fi

echo ""
echo "🎬 Ready to demo! Enjoy exploring H&S Layer!"
echo ""
