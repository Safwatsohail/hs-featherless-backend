# 🚀 Quick Start Guide

## One-Command Startup

```bash
./start.sh
```

That's it! The system will:
- ✅ Check dependencies
- ✅ Start backend on http://localhost:8000
- ✅ Start frontend on http://localhost:3000
- ✅ Show you next steps

## Manual Startup (if you prefer)

### 1. Start Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend (in new terminal)

```bash
cd frontend
python3 -m http.server 3000
```

## First Time Setup

### 1. Install Dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp backend/.env.example backend/.env

# Generate MASTER_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Edit backend/.env and paste the key
nano backend/.env  # or use your favorite editor
```

### 3. Get OpenRouter API Key

1. Go to https://openrouter.ai/keys
2. Create a free account
3. Generate an API key (starts with `sk-or-v1-`)
4. Keep it handy for testing

## Testing the System

### Method 1: Frontend UI (Recommended)

1. **Open:** http://localhost:3000

2. **Create Enhanced API Key:**
   ```bash
   curl -X POST http://localhost:8000/apikey \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test-user",
       "provider": "openrouter",
       "api_key": "sk-or-v1-YOUR-OPENROUTER-KEY"
     }'
   ```
   Copy the returned API key.

3. **Fill in the form:**
   - Enhanced API Key: (paste the key from step 2)
   - User ID: test-user
   - OpenRouter API Key: sk-or-v1-YOUR-OPENROUTER-KEY
   - Model: openrouter/free
   - Prompt: "Debug my Python API performance issues"

4. **Click both buttons:**
   - "Run Enhanced API"
   - "Run Normal API"

5. **Compare results:**
   - Enhanced shows: Skills, Tools, Memory, Lower cost
   - Normal shows: Just raw response, Higher cost

### Method 2: VS Code REST Client

1. **Install Extension:**
   - Open VS Code
   - Press Cmd+P (Mac) or Ctrl+P (Windows/Linux)
   - Type: `ext install humao.rest-client`

2. **Open Test File:**
   - Open `API_TESTS.http`
   - Update the `@apiKey` variable at the top

3. **Run Tests:**
   - Click "Send Request" above any test
   - See response in split pane

### Method 3: cURL

```bash
# Create API key
curl -X POST http://localhost:8000/apikey \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "provider": "openrouter",
    "api_key": "sk-or-v1-YOUR-KEY"
  }'

# Test enhanced API
curl -X POST http://localhost:8000/v1/run \
  -H "Authorization: Bearer YOUR-ENHANCED-KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Debug my Python API",
    "user_id": "test-user"
  }'
```

## What to Expect

### Enhanced API Response:
```json
{
  "output": "Detailed response with tools and memory...",
  "skill": "backend_debug",
  "tool_calls": [
    {"name": "code_analyzer", "result": "..."},
    {"name": "web_search", "result": "..."}
  ],
  "memory_hits": 3,
  "provider": "openrouter",
  "model": "anthropic/claude-3.5-sonnet",
  "usage": {
    "total_cost": 0.008
  }
}
```

### Normal API Response:
```json
{
  "choices": [{
    "message": {
      "content": "Generic response without tools..."
    }
  }],
  "usage": {
    "total_tokens": 1000,
    "total_cost": 0.03
  }
}
```

## Key Differences

| Feature | Enhanced API | Normal API |
|---------|-------------|------------|
| **Skills** | ✅ 1,080+ specialized skills | ❌ None |
| **Tools** | ✅ 50+ tools (web, code, DB) | ❌ None |
| **Memory** | ✅ Cross-API-key memory | ❌ None |
| **Cost** | ✅ $0.008/request (73% cheaper) | ❌ $0.03/request |
| **Quality** | ✅ Domain expertise + tools | ❌ Generic responses |

## Stopping the System

```bash
./stop.sh
```

Or manually:
```bash
# Find and kill processes
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

## Troubleshooting

### Port Already in Use

```bash
# Kill processes on ports
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### Backend Won't Start

```bash
# Check logs
tail -f backend.log

# Verify MASTER_KEY is set
cat backend/.env | grep MASTER_KEY

# Regenerate if needed
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Frontend Can't Connect

```bash
# Check if backend is running
curl http://localhost:8000/healthz

# Should return: {"ok": true}
```

### CORS Errors

Already fixed! The backend now includes CORS middleware.

## Next Steps

1. ✅ Test basic requests
2. ✅ Compare Enhanced vs Normal
3. ✅ Try complex tasks (see TESTING_GUIDE.md)
4. ✅ Test cross-API-key memory
5. ✅ Check cost savings
6. ✅ Review SDK examples (SDK_EXAMPLES.md)
7. ✅ Read production guide (PRODUCTION_READY.md)

## Documentation

- `TESTING_GUIDE.md` - Comprehensive testing scenarios
- `COMPETITIVE_ADVANTAGES.md` - Why we're better than OpenRouter
- `SDK_EXAMPLES.md` - Code examples in Python, JS, Go, Rust
- `PRODUCTION_READY.md` - Deployment and architecture
- `API_TESTS.http` - VS Code test cases

## Support

- Backend API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/healthz
- Skills List: http://localhost:8000/skills
- Tools List: http://localhost:8000/tools

---

**Ready to test! 🎉**

Open http://localhost:3000 and start comparing!
