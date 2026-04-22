# 🎯 Run Commands - Copy & Paste Ready

## 🚀 Quick Start (Recommended)

```bash
./start.sh
```

Then open: http://localhost:3000

---

## 📋 Step-by-Step Manual Setup

### 1️⃣ First Time Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Generate MASTER_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Edit .env and paste the key
nano .env
# Set: MASTER_KEY=<paste-the-key-here>

# Go back to root
cd ..
```

### 2️⃣ Start Backend

```bash
# From project root (not from backend directory!)
source backend/.venv/bin/activate
PYTHONPATH=. uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend running at:** http://localhost:8000

### 3️⃣ Start Frontend (New Terminal)

```bash
cd frontend
python3 -m http.server 3000
```

**Frontend running at:** http://localhost:3000

---

## 🧪 Testing Commands

### Create API Key

```bash
curl -X POST http://localhost:8000/apikey \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "provider": "openrouter",
    "api_key": "sk-or-v1-YOUR-OPENROUTER-KEY"
  }'
```

**Save the returned API key!**

### Test Enhanced API

```bash
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer YOUR-ENHANCED-KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Debug my Python API performance issues",
    "user_id": "test-user",
    "memory_scope": "workspace",
    "context_key": "test-project"
  }'
```

### Test Normal OpenRouter API

```bash
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer sk-or-v1-YOUR-KEY" \
  -H "Content-Type: application/json" \
  -H "HTTP-Referer: http://localhost:3000" \
  -d '{
    "model": "openrouter/free",
    "messages": [
      {"role": "user", "content": "Debug my Python API performance issues"}
    ]
  }'
```

### List Available Skills

```bash
curl http://localhost:8000/skills
```

### List Available Tools

```bash
curl http://localhost:8000/tools
```

### Health Check

```bash
curl http://localhost:8000/healthz
```

---

## 🛑 Stop Commands

### Stop All Services

```bash
./stop.sh
```

### Manual Stop

```bash
# Kill backend (port 8000)
lsof -ti:8000 | xargs kill -9

# Kill frontend (port 3000)
lsof -ti:3000 | xargs kill -9
```

---

## 🔧 Troubleshooting Commands

### Check if Ports are in Use

```bash
# Check port 8000 (backend)
lsof -i :8000

# Check port 3000 (frontend)
lsof -i :3000
```

### View Logs

```bash
# Backend logs (if using start.sh)
tail -f backend.log

# Frontend logs (if using start.sh)
tail -f frontend.log
```

### Verify Environment

```bash
# Check MASTER_KEY is set
cat backend/.env | grep MASTER_KEY

# Check Python version
python3 --version

# Check if virtual environment is active
which python
```

### Reinstall Dependencies

```bash
cd backend
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Reset Database

```bash
cd backend
rm -rf *.db  # Remove SQLite database
source .venv/bin/activate
python -c "from app.db.init_db import init_db; from app.db.session import engine; import asyncio; asyncio.run(init_db(engine))"
```

---

## 📊 Monitoring Commands

### Watch Backend Logs

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### Test All Endpoints

```bash
# Health
curl http://localhost:8000/healthz

# Skills
curl http://localhost:8000/skills | jq

# Tools
curl http://localhost:8000/tools | jq

# API Docs
open http://localhost:8000/docs
```

---

## 🎨 Frontend Testing

### Open in Browser

```bash
# macOS
open http://localhost:3000

# Linux
xdg-open http://localhost:3000

# Windows
start http://localhost:3000
```

### Alternative Frontend Servers

```bash
# Python 3
python3 -m http.server 3000

# Python 2
python -m SimpleHTTPServer 3000

# Node.js (if installed)
npx http-server -p 3000

# PHP (if installed)
php -S localhost:3000
```

---

## 🧪 VS Code Testing

### Install REST Client Extension

```bash
# Open VS Code
code .

# In VS Code Command Palette (Cmd+Shift+P or Ctrl+Shift+P)
# Type: ext install humao.rest-client
```

### Run Tests

1. Open `API_TESTS.http`
2. Update `@apiKey` variable at the top
3. Click "Send Request" above any test

---

## 🐳 Docker Commands (Optional)

### Build Docker Image

```bash
cd backend
docker build -t enhanced-ai-api .
```

### Run Docker Container

```bash
docker run -d \
  -p 8000:8000 \
  -e MASTER_KEY="your-key" \
  --name enhanced-api \
  enhanced-ai-api
```

### Stop Docker Container

```bash
docker stop enhanced-api
docker rm enhanced-api
```

---

## 📦 Production Commands

### Install Production Dependencies

```bash
cd backend
pip install gunicorn
```

### Run with Gunicorn

```bash
cd backend
source .venv/bin/activate
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Run with PM2 (Node.js process manager)

```bash
# Install PM2
npm install -g pm2

# Start backend
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name enhanced-api

# Start frontend
pm2 start "python3 -m http.server 3000" --name frontend

# View logs
pm2 logs

# Stop all
pm2 stop all
```

---

## 🔐 Security Commands

### Generate New MASTER_KEY

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Rotate API Keys

```bash
# List all API keys
curl http://localhost:8000/apikey

# Delete old key
curl -X DELETE http://localhost:8000/apikey/{key_id}

# Create new key
curl -X POST http://localhost:8000/apikey \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "provider": "openrouter",
    "api_key": "sk-or-v1-NEW-KEY"
  }'
```

---

## 📈 Performance Testing

### Load Test with Apache Bench

```bash
# Install Apache Bench
brew install httpd  # macOS
sudo apt-get install apache2-utils  # Linux

# Run load test
ab -n 1000 -c 10 \
  -H "Authorization: Bearer YOUR-KEY" \
  -H "Content-Type: application/json" \
  -p request.json \
  http://localhost:8000/v1/run
```

### Load Test with wrk

```bash
# Install wrk
brew install wrk  # macOS

# Run load test
wrk -t4 -c100 -d30s \
  -H "Authorization: Bearer YOUR-KEY" \
  -H "Content-Type: application/json" \
  --script=post.lua \
  http://localhost:8000/v1/run
```

---

## 🎯 Quick Reference

| Command | Description |
|---------|-------------|
| `./start.sh` | Start everything |
| `./stop.sh` | Stop everything |
| `curl http://localhost:8000/healthz` | Check backend health |
| `curl http://localhost:8000/skills` | List skills |
| `curl http://localhost:8000/tools` | List tools |
| `open http://localhost:3000` | Open frontend |
| `tail -f backend.log` | View backend logs |
| `lsof -ti:8000 \| xargs kill -9` | Kill backend |
| `lsof -ti:3000 \| xargs kill -9` | Kill frontend |

---

## 📚 Documentation Links

- **QUICKSTART.md** - Get started in 5 minutes
- **TESTING_GUIDE.md** - Comprehensive testing scenarios
- **README.md** - Project overview
- **API_TESTS.http** - VS Code test cases
- **http://localhost:8000/docs** - Interactive API documentation

---

**Ready to go! 🚀**

Run: `./start.sh` and open http://localhost:3000
