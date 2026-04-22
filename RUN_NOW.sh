#!/bin/bash

# Quick Run Script - Enhanced AI API
# This script checks if setup is done and runs the system

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    🚀 ENHANCED AI API - QUICK RUN                           ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d "backend/.venv" ]; then
    echo "⚠️  First time setup required!"
    echo ""
    echo "Run these commands:"
    echo ""
    echo "  cd backend"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "  cp .env.example .env"
    echo "  python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    echo "  # Edit .env and paste the key as MASTER_KEY"
    echo "  cd .."
    echo ""
    echo "Then run: ./start.sh"
    exit 1
fi

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Run these commands:"
    echo ""
    echo "  cd backend"
    echo "  cp .env.example .env"
    echo "  python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    echo "  # Edit .env and paste the key as MASTER_KEY"
    echo "  cd .."
    echo ""
    echo "Then run: ./start.sh"
    exit 1
fi

# Check if MASTER_KEY is set
if ! grep -q "MASTER_KEY=" backend/.env || grep -q "MASTER_KEY=$" backend/.env; then
    echo "⚠️  MASTER_KEY not set in .env!"
    echo ""
    echo "Generate a key:"
    echo ""
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    echo ""
    echo "Edit backend/.env and set: MASTER_KEY=<paste-key-above>"
    echo ""
    echo "Then run: ./start.sh"
    exit 1
fi

# Everything is ready, start the system
echo "✅ Setup complete! Starting system..."
echo ""
./start.sh
