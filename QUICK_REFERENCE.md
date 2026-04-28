# ⚡ Quick Reference Card

## 🚀 Start/Stop

```bash
./start.sh   # Start everything
./stop.sh    # Stop everything
```

## 🌐 URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

## 🔑 Generate Aurora Key

```bash
# 1. Store Featherless key
curl -X POST http://localhost:8000/apikey \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "provider": "featherless",
    "api_key": "fl_YOUR_FEATHERLESS_KEY"
  }'

# 2. Generate Aurora key
curl -X POST http://localhost:8000/auth/issue-key \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "name": "My Key",
    "scopes": ["chat", "memory", "tools", "skills"]
  }'
```

## 💬 Basic Chat

```bash
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "Your question here",
    "memory_scope": "user"
  }'
```

## 🧠 Memory

```bash
# Store
curl -X POST http://localhost:8000/v1/memory \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "text": "I prefer JSON responses",
    "kind": "preference",
    "memory_scope": "user"
  }'

# Retrieve
curl -X POST http://localhost:8000/v1/memory/context \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "query": "preferences",
    "memory_scope": "user"
  }'
```

## 🎯 Skills

```bash
# List all
curl http://localhost:8000/v1/skills

# Invoke specific
curl -X POST http://localhost:8000/v1/skills/research \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "Latest AI developments"
  }'
```

## 🛠️ Tools

```bash
# List all
curl http://localhost:8000/tools

# Execute
curl -X POST http://localhost:8000/v1/tools/web_search \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {"query": "React 19 features"}
  }'
```

## 📊 Compare

```bash
curl -X POST http://localhost:8000/compare \
  -H "Authorization: Bearer aurora_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "What are the latest AI developments?",
    "provider": "featherless",
    "model": "gpt-4.1-mini"
  }'
```

## 🔍 Debug

```bash
# Health check
curl http://localhost:8000/healthz

# Check logs
tail -f backend.log
tail -f frontend.log

# Kill processes
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Check configuration
cat backend/.env | grep HOST
# Should be: HOST=127.0.0.1
```

## 📝 Memory Scopes

| Scope | Sharing |
|-------|---------|
| `user` | All keys for same user |
| `workspace` | Same project |
| `conversation` | Single conversation |
| `global` | All users |

## 🔒 Security

- Backend: `127.0.0.1` (local only)
- Keys: Encrypted with Fernet
- Database: Local SQLite
- No external access

## 📚 Docs

- `DEVELOPER_GUIDE.md` - Full guide
- `AURORA_API_USAGE.md` - API usage
- `LOCAL_SETUP_COMPLETE.md` - Setup
- `FIXES_APPLIED.md` - What was fixed
