# 🚀 H&S Layer — Enhanced AI API
youtube video link :::: - https://youtu.be/JP9eD4NWDJc
> Transform any LLM into a 10x better AI with skills, tools, and memory

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---
youtube video link :::: - https://youtu.be/JP9eD4NWDJc




## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Complete Setup Tutorial](#-complete-setup-tutorial)
3. [How It Works](#-how-it-works)
4. [Raw vs Enhanced](#-raw-vs-enhanced)
5. [API Reference](#-api-reference)
6. [Troubleshooting](#-troubleshooting)

---

## ⚡ Quick Start

```bash
git clone https://github.com/Safwatsohail/hs-featherless-backend.git
cd hs-featherless-backend
./START.sh
```

Browser opens at **http://localhost:3000**. Done.

To stop:
```bash
./STOP.sh
```

---

## 🎓 Complete Setup Tutorial

### Prerequisites

You need:
- **Python 3.8+** — check with `python3 --version`
- **Git** — check with `git --version`
- **2GB RAM** minimum
- **Internet connection** for first-time setup

**Install Python if missing:**

**Mac:**
```bash
brew install python3
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Windows:**
Download from https://www.python.org/downloads/ — **check "Add Python to PATH"**

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Safwatsohail/hs-featherless-backend.git
cd hs-featherless-backend
```

Verify you see these files:
```bash
ls -la
```

You should see: `backend/`, `frontend/`, `START.sh`, `STOP.sh`, `README.md`

---

### Step 2 — Run START.sh

```bash
chmod +x START.sh STOP.sh
./START.sh
```

This single command:
1. ✅ Checks Python version
2. ✅ Creates a virtual environment
3. ✅ Installs all dependencies (~30 seconds on first run)
4. ✅ Initializes the database
5. ✅ Creates `.env` configuration
6. ✅ Starts the backend (port 8000)
7. ✅ Starts the frontend (port 3000)
8. ✅ Opens your browser automatically

**Expected output:**
```
🔍 Checking Python...          ✅ Python 3.x found
💻 OS: Mac
🔧 Setting up backend...
   Creating virtual environment...
   Installing dependencies...   (first run: ~30 seconds)
✅ Backend ready
🗄️  Initializing database...   ✅ Database ready
⚙️  Creating .env...            ✅ Configuration ready
🚀 Starting backend...          ✅ Backend started (PID: 12345)
🚀 Starting frontend...         ✅ Frontend started (PID: 12346)
🎉 Ready! Opening browser...
```

**Total time:** 30–60 seconds on first run, ~5 seconds after that.

---

### Step 3 — Explore the Dashboard

Two options appear on screen:

**Option 1: View Interactive Demo**
- 9-step cinematic walkthrough
- No setup needed
- Shows the complete flow from onboarding to A/B comparison

**Option 2: Continue with SSO**
- Jump straight into the live dashboard
- Test the A/B comparison with your own prompts
- Explore memory, skills, and tools

---

### Step 4 — Stop the Application

```bash
./STOP.sh
```

This stops both backend and frontend servers.

---

## 🏗 How It Works

### The Two Paths

When you send a prompt, the system runs **two parallel paths**:

#### Raw Model (Right Pane)
- ❌ No skills
- ❌ No tools
- ❌ No memory
- ❌ No formatting
- 🎲 Temperature 0.95 (random, imprecise)
- Direct LLM call only

**Result:** Basic, unstructured response

#### Enhanced Model (Left Pane)
- ✅ 1,080+ skills (auto-selected)
- ✅ 55+ tools (intelligent selection)
- ✅ 3-layer memory system
- ✅ Production-ready code formatting
- 🎯 Temperature 0.1–0.7 (optimized)
- Full orchestration pipeline

**Result:** Precise, structured, tool-enhanced response

---

### The Enhanced Pipeline (10 Stages)

```
User Message
    ↓
[STAGE 1] AUTH & SETUP
    ├── Validate Aurora key
    ├── Fetch encrypted provider key
    └── Create LLM clients
    ↓
[STAGE 2] SKILL ROUTING
    ├── Keyword match (instant)
    │   "write/code/python" → code_assistant
    │   "debug/fix/error" → debug
    │   "research/latest" → deep_research
    │
    └── No match? → Planner model decides
    ↓
[STAGE 3] MEMORY RETRIEVAL
    ├── Short-term: last 5 messages
    ├── Vector memory: semantic search (top 10)
    └── Auto-extracted facts
    ↓
[STAGE 4] SYSTEM PROMPT CONSTRUCTION
    ├── Skill template
    ├── Memory context
    ├── Recent conversation
    ├── Enhanced capabilities
    └── Response guidelines
    ↓
[STAGE 5] TOOL SELECTION
    ├── Skip check: greeting? → no tools
    ├── Smart keyword matching
    └── Planner decides if needed
    ↓
[STAGE 6] TOOL EXECUTION
    ├── code_exec → Python/JS sandbox
    ├── web_search → Current information
    ├── math_exec → Mathematical expressions
    ├── file_read → Local files
    └── ... 50+ more tools
    ↓
[STAGE 7] LLM GENERATION
    ├── Temperature optimized by task
    ├── Full context sent to LLM
    └── Streaming response
    ↓
[STAGE 8] RESPONSE CLEANUP
    ├── Remove meta-commentary
    ├── Fix code formatting
    ├── Auto-detect language
    └── Remove duplicates
    ↓
[STAGE 9] MEMORY STORAGE
    ├── Save conversation
    ├── Extract facts
    └── Store in vector DB
    ↓
[STAGE 10] RESPONSE RETURNED
    ├── Formatted output
    ├── Tool calls & results
    ├── Memory hits
    └── Usage metrics
```

---

## 📊 Raw vs Enhanced

| Feature | Raw | Enhanced |
|---------|-----|----------|
| **Skills** | ❌ 0 | ✅ 1,080+ |
| **Tools** | ❌ 0 | ✅ 55+ |
| **Memory** | ❌ None | ✅ 3-layer |
| **Code Quality** | ⚠️ Basic | ✅ Production |
| **Type Hints** | ❌ No | ✅ Always |
| **Docstrings** | ❌ No | ✅ Comprehensive |
| **Error Handling** | ❌ No | ✅ try/except |
| **Syntax Highlighting** | ❌ Plain text | ✅ VS Code theme |
| **Temperature** | 🎲 0.95 | 🎯 0.1–0.7 |
| **System Prompt** | 📝 1 line | 🔥 Full context |

---

### Example: "Write a Python calculator"

**Raw Model:**
```
a calculator in python would be something like:
x = input()
y = input()
print(x + y)
```

**Enhanced Model:**
```python
"""Production-ready calculator with type hints and error handling."""

def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Subtract two numbers."""
    return a - b

class Calculator:
    """Simple calculator with basic operations."""
    
    def __init__(self):
        self.last_result = 0
    
    def calculate(self, operation: str, a: float, b: float) -> float:
        """Execute calculation with error handling."""
        try:
            if operation == "+":
                self.last_result = add(a, b)
            elif operation == "-":
                self.last_result = subtract(a, b)
            else:
                raise ValueError(f"Unknown operation: {operation}")
            return self.last_result
        except Exception as e:
            print(f"Error: {e}")
            return 0

# Usage
calc = Calculator()
result = calc.calculate("+", 5, 3)
print(f"Result: {result}")
```

---

## 📡 API Reference

### Authentication

All endpoints require:
```
Authorization: Bearer aurora_live_xxxxx
```

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/compare` | A/B compare raw vs enhanced |
| `POST` | `/v1/run` | Enhanced chat (skills + tools + memory) |
| `POST` | `/auth/issue-key` | Generate Aurora key |
| `POST` | `/apikey` | Store provider API key |
| `GET` | `/v1/skills` | List all skills |
| `GET` | `/tools` | List all tools |
| `GET` | `/healthz` | Health check |

### POST /v1/compare — A/B Comparison

```bash
curl -X POST http://localhost:8000/v1/compare \
  -H "Authorization: Bearer aurora_live_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "Write a Python calculator",
    "provider": "openrouter",
    "model": "openrouter/auto"
  }'
```

**Response:**
```json
{
  "baseline": {
    "title": "Raw Model API",
    "output": "basic response, no tools, no memory",
    "metrics": {
      "latency_ms": 900,
      "tool_count": 0,
      "memory_hits": 0,
      "estimated_accuracy": 58
    }
  },
  "tuned": {
    "title": "HNS Tuned API",
    "skill": "code_assistant",
    "output": "production-ready response with syntax highlighting",
    "tool_calls": [{ "name": "code_exec" }],
    "metrics": {
      "latency_ms": 1800,
      "tool_count": 1,
      "memory_hits": 2,
      "estimated_accuracy": 86
    }
  },
  "delta": {
    "accuracy_gap": 28,
    "tool_advantage": 1,
    "memory_advantage": 2,
    "efficiency_gap": 12
  }
}
```

---

## � Troubleshooting

### "Permission denied" on START.sh
```bash
chmod +x START.sh STOP.sh
./START.sh
```

### "Python not found"
**Mac:**
```bash
brew install python3
```

**Linux:**
```bash
sudo apt install python3 python3-pip python3-venv
```

**Windows:**
https://www.python.org/downloads/ — check "Add Python to PATH"

### "Port already in use"
```bash
./STOP.sh && sleep 2 && ./START.sh
```

If still stuck:
```bash
# Mac/Linux
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### "Module not found"
```bash
cd backend
source .venv/bin/activate  # Mac/Linux
# or: .venv\Scripts\activate  # Windows
pip install -r requirements.txt
cd ..
./START.sh
```

### "Database locked"
```bash
./STOP.sh
rm backend/ai_orchestrator.db
./START.sh
```

### Backend not responding
```bash
curl http://localhost:8000/healthz
tail -f backend.log
```

### Browser doesn't open
Manually go to: http://localhost:3000

### Slow first install
Normal — pip downloads ~50 packages. Should be under 2 minutes on a decent connection.

### Virtual environment broken
```bash
cd backend
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# or: .venv\Scripts\activate  # Windows
pip install -r requirements.txt
cd ..
./START.sh
```

---

## 📁 Project Structure

```
hs-featherless-backend/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, logging
│   │   ├── db/            # Database setup
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routes/        # API endpoints
│   │   ├── schemas/       # Request/response schemas
│   │   ├── services/      # Business logic
│   │   └── utils/         # Helpers
│   ├── requirements.txt
│   └── .env               # Auto-created
│
├── frontend/
│   ├── index.html         # Main UI
│   ├── main.js            # Frontend logic
│   └── style.css          # Styling
│
├── START.sh               # Setup & start
├── STOP.sh                # Stop servers
└── README.md              # This file
```

---

## 🚀 Quick Reference

```bash
./START.sh                          # setup + start
./STOP.sh                           # stop

curl http://localhost:8000/healthz  # health check
tail -f backend.log                 # backend logs
tail -f frontend.log                # frontend logs

http://localhost:3000               # frontend
http://localhost:8000/docs          # swagger docs
```

---

## 📄 License

MIT — see LICENSE file.

---

**Built with ❤️ for Featherless.ai**
