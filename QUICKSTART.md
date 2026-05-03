# ⚡ Quick Start Guide

Get H&S Layer running in 5 minutes!

---

## 🚀 Step 1: Clone & Install

```bash
# Clone the repository
git clone https://github.com/Safwatsohail/hs-featherless-backend.git
cd hs-featherless-backend

# Install backend dependencies
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

---

## 🎯 Step 2: Start Servers

```bash
./START_SERVERS.sh
```

**This will:**
- ✅ Start backend on http://localhost:8000
- ✅ Start frontend on http://localhost:3000
- ✅ Store your OpenRouter API key
- ✅ Generate your Aurora enhanced key
- ✅ Display your credentials

**Output:**
```
✅ BOTH SERVERS RUNNING!

🔥 Backend:  http://localhost:8000
🎨 Frontend: http://localhost:3000

🔑 YOUR CREDENTIALS:
   Aurora Key:     aurora_live_xxxxx
   User ID:        00000000-0000-0000-0000-000000000001
```

---

## 🎨 Step 3: Open Dashboard

Open http://localhost:3000 in your browser

You'll see:
- **Landing Page** - Overview of features
- **Dashboard** - Main interface with tabs:
  - A/B Chat - Compare raw vs enhanced
  - Memory - View stored facts
  - Skills - Browse 1,080+ skills
  - Tools - View 55+ tools
  - API Key - Manage keys
  - Dev Docs - Code examples

---

## 💬 Step 4: Test It Out

### In the Dashboard:

1. Click **"A/B Chat"** tab
2. Your Aurora key and User ID are pre-filled
3. Type: `"Write a Python function to calculate fibonacci"`
4. Click **"Run Comparison"**
5. Watch both responses appear side-by-side!

### Via API:

```bash
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "Write a Python function to add two numbers",
    "provider": "openrouter",
    "model": "openrouter/auto",
    "memory_scope": "user"
  }'
```

---

## 🧪 Step 5: Test Memory

```bash
# Store some facts
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "My name is John and I prefer TypeScript",
    "provider": "openrouter",
    "model": "openrouter/auto",
    "memory_scope": "user"
  }'

# Check memory tab in frontend
# You should see:
# - "User's name is John"
# - "User prefers TypeScript"
```

---

## 🛑 Stop Servers

```bash
./STOP_SERVERS.sh
```

---

## 🎯 Next Steps

- **[Developer Guide](DEVELOPER_GUIDE.md)** - Integrate into your project
- **[Testing Guide](TESTING_GUIDE.md)** - Comprehensive testing
- **[API Reference](http://localhost:8000/docs)** - Full API documentation

---

## 🆘 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 $(lsof -t -i:8000)

# Restart
./START_SERVERS.sh
```

### Frontend won't start
```bash
# Check if port 3000 is in use
lsof -i :3000

# Kill existing process
kill -9 $(lsof -t -i:3000)

# Restart
./START_SERVERS.sh
```

### API key not working
```bash
# Regenerate key
curl -X POST http://localhost:8000/auth/issue-key \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "name": "New Key",
    "scopes": ["chat", "memory", "tools", "skills"]
  }'
```

---

**You're all set! Start building with H&S Layer! 🚀**
