# 🚀 H&S Layer — Enhanced AI API

> Transform any LLM into a 10x better AI with skills, tools, and memory

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Setup Tutorial](#-setup-tutorial)
3. [How the Backend Works](#-how-the-backend-works)
4. [Aurora API Key — How It Works](#-aurora-api-key--how-it-works)
5. [The Planner (Mini) Model](#-the-planner-mini-model)
6. [Complete Backend Pipeline](#-complete-backend-pipeline)
7. [Raw vs Enhanced](#-raw-vs-enhanced)
8. [Test Examples](#-test-examples)
9. [API Reference](#-api-reference)
10. [Troubleshooting](#-troubleshooting)
11. [Project Structure](#-project-structure)

---

## ⚡ Quick Start

```bash
git clone https://github.com/Safwatsohail/hs-featherless-backend.git
cd hs-featherless-backend
./START.sh
```

Browser opens automatically at **http://localhost:3000**. That's it.

To stop:
```bash
./STOP.sh
```

---

## 🎓 Setup Tutorial

### Step 1 — Check Requirements

You need:
- **Python 3.8+** — check with `python3 --version`
- **Git** — check with `git --version`
- **2GB RAM** minimum
- **Internet connection** for first-time dependency install

**Install Python if missing:**

Mac: `brew install python3`
Linux: `sudo apt install python3 python3-pip python3-venv`
Windows: https://www.python.org/downloads/ — check "Add Python to PATH"

---

### Step 2 — Clone the Repo

```bash
git clone https://github.com/Safwatsohail/hs-featherless-backend.git
cd hs-featherless-backend
```

After `cd`, run `ls` — you should see `backend/`, `frontend/`, `START.sh`, `STOP.sh`.

---

### Step 3 — Run START.sh

```bash
./START.sh
```

This single command does everything:

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

### Step 4 — Explore

Two options on the screen:

- **"View Interactive Demo"** — 9-step cinematic walkthrough, no setup needed
- **"Continue with SSO"** — jump straight into the live dashboard

---

### Step 5 — Stop

```bash
./STOP.sh
```

---

## 🏗 How the Backend Works

The backend is a **FastAPI** application running on port 8000. It acts as an intelligent middleware layer between your frontend and any LLM provider (OpenRouter, Featherless).

When the app starts it:
- Loads **1,080+ built-in skills** into the database
- Initialises a **vector store** (ChromaDB or in-memory) for semantic memory
- Sets up an **encrypted key store** (AES) for provider API keys
- Registers all API routes

The core idea: instead of calling an LLM directly, every request goes through the **Orchestrator** — a pipeline that adds skills, tools, and memory before the LLM ever sees the message.

---

## 🔑 Aurora API Key — How It Works

The Aurora key (`aurora_live_xxxxx`) is your identity token for the H&S Layer API. Here is the exact flow:

### Step 1 — Issue a key (one time)

```
POST /auth/issue-key
Body: { user_id, name, scopes: ["run", "memory", "tools"] }

→ Backend generates:  aurora_live_<random_24_chars>
→ Hashes it with SHA-256
→ Stores the HASH in the database (never the raw key)
→ Returns the raw key ONCE — frontend must save it
```

### Step 2 — Store your provider key (one time)

The Aurora key identifies you, but the backend also needs your actual OpenRouter or Featherless key to call the LLM:

```
POST /apikey
Header: Authorization: Bearer aurora_live_xxxxx
Body: { user_id, provider: "openrouter", api_key: "sk-or-v1-..." }

→ Backend encrypts the provider key with AES
→ Stores the encrypted version in SQLite
→ Decrypts it on every request — never exposed
```

### Step 3 — Every API call

Frontend sends the Aurora key on every request as a Bearer token:

```
POST /v1/compare
Header: Authorization: Bearer aurora_live_xxxxx
Body: { user_id, input, provider, model }
```

Backend validates it like this:

```
1. Read Authorization header → extract raw key
2. SHA-256 hash the raw key
3. Look up the hash in aurora_api_keys table
4. If found → get user_id + scopes → proceed
5. If not found → 401 Unauthorized
6. If TEST_MODE_ENABLED in .env → use demo key automatically (no header needed)
```

### Two ways to send the key

```bash
# Option 1 — x-aurora-key header
curl -H "x-aurora-key: aurora_live_xxxxx" ...

# Option 2 — Bearer token (what the frontend uses)
curl -H "Authorization: Bearer aurora_live_xxxxx" ...
```

---

## 🧠 The Planner (Mini) Model

Your system runs **two models** on every enhanced request — a cheap fast one to plan, and the main one to respond.

### The two models

```
PLANNER MODEL (mini/fast)          MAIN MODEL (full/smart)
─────────────────────────          ──────────────────────
Config: DECISION_LLM_MODEL         Config: DEFAULT_LLM_MODEL
Default: gpt-4.1-nano              Default: gpt-4.1-mini

Runs FIRST                         Runs SECOND
Makes decisions                    Generates the actual answer
Cheap + fast                       Full quality
```

### What the planner decides

**1. Which skill to use** — if keyword matching doesn't find a clear match, the planner reads the user message and picks the best skill from the 1,080+ catalog.

**2. Which tools to call** — if smart keyword matching doesn't trigger a tool, the planner looks at the message + available tool specs and decides which tools to run.

### When the planner is skipped

For common patterns, keyword matching handles it instantly without calling the planner at all:

```
"write/create/code/python"  → code_assistant skill  (no planner needed)
"debug/fix/error/bug"       → debug skill            (no planner needed)
"research/analyze/latest"   → deep_research skill    (no planner needed)
"review/optimize/refactor"  → review skill           (no planner needed)
```

The planner only kicks in for ambiguous queries where keywords don't match.

### Configure in .env

```bash
DECISION_LLM_PROVIDER=openrouter   # can be different from main provider
DECISION_LLM_MODEL=gpt-4.1-nano    # cheap fast model for planning
DEFAULT_LLM_PROVIDER=openrouter    # main provider
DEFAULT_LLM_MODEL=gpt-4.1-mini     # main model for responses
```

If `DECISION_LLM_PROVIDER` is not set, the planner uses the same provider as the main model — just a cheaper/faster model variant.

---

## 🔄 Complete Backend Pipeline

This is the exact sequence of what happens from the moment a user sends a message to when they get a response.

### The two parallel paths

When you call `/v1/compare`, the backend runs **two paths simultaneously** — one raw, one enhanced — and returns both.

---

### RAW PATH (right pane — dumb baseline)

```
User message
    │
    ▼
Direct LLMClient call
    │
    ├── System prompt: "You are a basic AI. Answer briefly."
    ├── Temperature: 0.9 (random, imprecise)
    ├── No skills
    ├── No tools
    └── No memory
    │
    ▼
Raw LLM response → returned as baseline{}
```

---

### ENHANCED PATH (left pane — full pipeline)

```
User message
    │
    ▼
─────────────────────────────────────────
STAGE 1 — AUTH & SETUP
─────────────────────────────────────────
    │
    ├── Validate Aurora key (hash lookup in DB)
    ├── Fetch + decrypt stored OpenRouter/Featherless key
    ├── Create LLMClient (main model)
    └── Create planner LLMClient (mini model)
    │
    ▼
─────────────────────────────────────────
STAGE 2 — SKILL ROUTING
─────────────────────────────────────────
    │
    ├── Keyword match (instant, no LLM):
    │       "write/code/python"  → code_assistant
    │       "debug/fix/error"    → debug
    │       "research/latest"    → deep_research
    │       "review/optimize"    → review
    │       "sql/dashboard"      → data_analyst
    │
    └── No match? → Planner model (gpt-4.1-nano) reads
                    message + skill catalog → picks best skill
    │
    ▼
─────────────────────────────────────────
STAGE 3 — MEMORY RETRIEVAL
─────────────────────────────────────────
    │
    ├── Short-term memory: last 5 messages from SQLite
    │
    ├── Vector memory: semantic search across all stored facts
    │       top 10 results, filtered to score > 0.5
    │       e.g. "User's name is Alex", "User prefers Python"
    │
    └── Facts auto-extracted after each turn:
            names, preferences, projects, technologies,
            goals, experience, location, company
    │
    ▼
─────────────────────────────────────────
STAGE 4 — SYSTEM PROMPT CONSTRUCTION
─────────────────────────────────────────
    │
    Assembled in this order:
    │
    ├── [1] Skill template (e.g. code_assistant prompt)
    ├── [2] Memory context (relevant facts from vector search)
    ├── [3] Recent conversation (last 5 messages)
    ├── [4] Enhanced capabilities section (tools + skills + memory)
    ├── [5] Response excellence guidelines (code structure rules)
    └── [6] Critical rules (no meta-commentary, one code block, etc.)
    │
    ▼
─────────────────────────────────────────
STAGE 5 — TOOL SELECTION
─────────────────────────────────────────
    │
    ├── Skip check: is it a greeting? (hi/hello/thanks) → no tools
    ├── Skip check: < 15 chars and not code-related? → no tools
    │
    ├── Smart keyword matching:
    │       ".pdf" in input          → pdf_analyze
    │       "latest/current/news"    → web_search
    │       "calculate/compute/math" → math_exec
    │       "execute/run/test code"  → code_exec
    │       "read file/open file"    → file_read
    │       "analyze image"          → image_analyze
    │       "write/create/generate"  → code_exec (for code)
    │
    └── No match? → Planner model decides which tools to use
    │
    ▼
─────────────────────────────────────────
STAGE 6 — TOOL EXECUTION
─────────────────────────────────────────
    │
    For each selected tool:
    │
    ├── code_exec      → runs Python/JS in sandboxed env
    ├── math_exec      → evaluates mathematical expressions
    ├── web_search     → searches the web via API
    ├── deep_search    → multi-page deep research
    ├── file_read      → reads local files
    ├── image_analyze  → analyzes images with vision model
    ├── pdf_analyze    → extracts and analyzes PDF content
    ├── sql_exec       → executes SQL queries
    ├── api_call       → makes HTTP requests
    └── bash           → runs bash commands (restricted)
    │
    Tool results injected into messages as:
    "Tool Results: ⚡ Code Execution
     Raw Data: {output: '...'}
     Use these results to answer."
    │
    ▼
─────────────────────────────────────────
STAGE 7 — LLM GENERATION
─────────────────────────────────────────
    │
    Temperature optimised by query type:
    ├── "write/create/code/function" → 0.1 (very precise)
    ├── "brainstorm/creative/story"  → 0.7 (more varied)
    └── everything else              → 0.2 (balanced)
    │
    Messages sent to LLM:
    ├── [system] full system prompt (skill + memory + guidelines)
    ├── [user]   original user message
    └── [user]   tool results (if any tools ran)
    │
    → Calls OpenRouter / Featherless API
    → Returns: content, token usage, raw response
    │
    ▼
─────────────────────────────────────────
STAGE 8 — RESPONSE CLEANUP
─────────────────────────────────────────
    │
    ├── Remove meta-commentary ("As an AI...", "I apologize...")
    ├── Fix malformed code blocks (missing backticks, wrong format)
    ├── Auto-detect language if missing (python/javascript/typescript)
    ├── Remove duplicate code blocks (keep first/best)
    ├── Clean up excessive newlines (max 3)
    ├── Remove HTML artifacts (class="...", <tags>)
    └── Prepend tool usage header ("*Used: ⚡ Code Execution*")
    │
    ▼
─────────────────────────────────────────
STAGE 9 — MEMORY STORAGE
─────────────────────────────────────────
    │
    ├── Save user message to SQLite (messages table)
    ├── Save assistant reply to SQLite (messages table)
    ├── Extract facts from conversation → store in vector DB
    │       "My name is Alex" → "User's name is Alex"
    │       "I prefer Python" → "User prefers Python"
    │       "I work at Google" → "User works at Google"
    └── Store structured turn data (skill, tools used, token count)
    │
    ▼
─────────────────────────────────────────
STAGE 10 — RESPONSE RETURNED
─────────────────────────────────────────
    │
    OrchestratorResult:
    ├── conversation_id  → UUID for this conversation
    ├── skill            → "code_assistant"
    ├── output           → cleaned, formatted response
    ├── tool_calls       → [{ name: "code_exec", input: {...} }]
    ├── tool_results     → [{ name, output, metadata }]
    ├── provider         → "openrouter"
    ├── model            → "openrouter/auto"
    ├── memory_hits      → 2
    └── usage            → { prompt_tokens, completion_tokens, total_tokens }
```

---

### Final response shape from /v1/compare

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

## 📊 Raw vs Enhanced

| Feature | Raw Model | Enhanced Model |
|---------|-----------|----------------|
| **Skills** | ❌ 0 | ✅ 1,080+ auto-selected |
| **Tools** | ❌ 0 | ✅ 55+ intelligent selection |
| **Memory** | ❌ None | ✅ 3-layer system |
| **Planner model** | ❌ None | ✅ gpt-4.1-nano decides |
| **Code quality** | ⚠️ Basic | ✅ Production-ready |
| **Type hints** | ❌ No | ✅ Always |
| **Docstrings** | ❌ No | ✅ Comprehensive |
| **Error handling** | ❌ No | ✅ try/except + validation |
| **Syntax highlighting** | ❌ Plain text | ✅ VS Code Dark+ theme |
| **Temperature** | 🎲 0.9 random | 🎯 0.1–0.7 optimised |
| **System prompt** | 📝 1 line | 🔥 Full context + guidelines |
| **Response cleanup** | ❌ None | ✅ 8-step pipeline |

---

## 🧪 Test Examples

### Greeting
Input: `hi`
- **Enhanced** → "Hello! How can I help you today?" (short, no code)
- **Raw** → "Hello" (very basic)

### Code generation
Input: `Write a Python calculator`
- **Enhanced** → production code, type hints, docstrings, syntax highlighting, code_exec tool used
- **Raw** → basic code, no structure, plain text

### Research
Input: `What's the latest version of Python?`
- **Enhanced** → uses web_search tool, current accurate answer
- **Raw** → possibly outdated answer, no tool

### Math
Input: `Calculate 2^10`
- **Enhanced** → uses math_exec tool, answer: 1024
- **Raw** → "approximately 1000" (wrong)

---

## 📡 API Reference

### Authentication

All endpoints (except `/auth/issue-key` and `/healthz`) require:
```
Authorization: Bearer aurora_live_xxxxx
```
or:
```
x-aurora-key: aurora_live_xxxxx
```

---

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/issue-key` | Generate an Aurora enhanced key |
| `POST` | `/apikey` | Store a provider API key (encrypted) |
| `POST` | `/v1/run` | Enhanced chat (skills + tools + memory) |
| `POST` | `/v1/compare` | A/B compare raw vs enhanced |
| `POST` | `/v1/skills/{name}` | Invoke a specific skill |
| `GET`  | `/v1/skills` | List all available skills |
| `POST` | `/v1/tools/{name}` | Execute a specific tool |
| `GET`  | `/tools` | List all tools |
| `POST` | `/v1/memory` | Store a memory fact |
| `POST` | `/v1/memory/context` | Retrieve memory context |
| `GET`  | `/healthz` | Health check |
| `GET`  | `/docs` | Interactive API docs (Swagger) |

---

### POST /v1/run — Enhanced chat

```bash
curl -X POST http://localhost:8000/v1/run \
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
  "conversation_id": "uuid",
  "skill": "code_assistant",
  "output": "Here is a production-ready calculator:\n\n```python\n...",
  "provider": "openrouter",
  "model": "openrouter/auto",
  "tool_calls": [{ "name": "code_exec", "input": {} }],
  "metrics": {
    "memory_hits": 2,
    "tool_count": 1,
    "usage": { "prompt_tokens": 450, "completion_tokens": 320, "total_tokens": 770 }
  }
}
```

---

### POST /v1/compare — A/B comparison

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

Returns `baseline{}` (raw) + `tuned{}` (enhanced) + `delta{}` (difference metrics).

---

### POST /auth/issue-key — Generate Aurora key

```bash
curl -X POST http://localhost:8000/auth/issue-key \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "name": "my-app",
    "scopes": ["run", "memory", "tools", "skills"]
  }'
```

**Response:**
```json
{
  "api_key": "aurora_live_xxxxx",
  "user_id": "...",
  "scopes": ["run", "memory", "tools", "skills"]
}
```

Save `api_key` — it is shown **once only**.

---

### POST /apikey — Store provider key

```bash
curl -X POST http://localhost:8000/apikey \
  -H "Authorization: Bearer aurora_live_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "provider": "openrouter",
    "api_key": "sk-or-v1-..."
  }'
```

---

### Memory scopes

| Scope | Shared across | Use case |
|-------|--------------|----------|
| `user` | All keys for same user_id | Personal preferences, facts |
| `workspace` | Same context_key | Project-specific knowledge |
| `conversation` | Single conversation_id | Private session |
| `global` | All users | Shared knowledge base |

---

## 🔧 Troubleshooting

### "Permission denied" on START.sh
```bash
chmod +x START.sh STOP.sh
./START.sh
```

### "Python not found"
Mac: `brew install python3`
Linux: `sudo apt install python3 python3-pip python3-venv`
Windows: https://www.python.org/downloads/ — check "Add Python to PATH"

### "Port already in use"
```bash
./STOP.sh && sleep 2 && ./START.sh
```
If still stuck:
```bash
lsof -ti:8000 | xargs kill -9   # Mac/Linux
lsof -ti:3000 | xargs kill -9
```

### "Module not found"
```bash
cd backend
source .venv/bin/activate
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
curl http://localhost:8000/healthz   # should return {"ok":true}
tail -f backend.log                  # check for errors
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
source .venv/bin/activate
pip install -r requirements.txt
cd ..
./START.sh
```

---

## 📁 Project Structure

```
hs-featherless-backend/
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          # All settings (providers, timeouts, models)
│   │   │   └── logging.py         # Logging configuration
│   │   ├── db/
│   │   │   ├── session.py         # SQLite async session
│   │   │   └── init_db.py         # Schema creation on startup
│   │   ├── models/
│   │   │   ├── conversation.py    # Conversations + messages tables
│   │   │   ├── memory_metadata.py # Structured memory facts table
│   │   │   ├── aurora_api_key.py  # Aurora key table
│   │   │   └── api_key.py         # Provider key table (encrypted)
│   │   ├── routes/
│   │   │   ├── public_api.py      # /v1/run, /v1/compare, /v1/memory
│   │   │   ├── aurora_auth.py     # /auth/issue-key
│   │   │   ├── apikey.py          # /apikey
│   │   │   ├── skills.py          # /skills
│   │   │   └── tools.py           # /tools
│   │   ├── services/
│   │   │   ├── orchestrator.py    # Core pipeline (skill→memory→tools→LLM)
│   │   │   ├── llm_client.py      # HTTP calls to OpenRouter/Featherless
│   │   │   ├── skill_engine.py    # 1,080+ skill definitions + routing
│   │   │   ├── memory_engine.py   # Short-term + vector memory
│   │   │   ├── tool_engine.py     # 55+ tool executors
│   │   │   ├── vector_store.py    # ChromaDB or in-memory embeddings
│   │   │   ├── cache_layer.py     # Redis or local cache
│   │   │   ├── aurora_auth_service.py  # Aurora key issue + validate
│   │   │   └── api_key_service.py # Encrypted provider key storage
│   │   └── utils/
│   │       └── crypto.py          # AES encryption for stored keys
│   ├── requirements.txt
│   └── .env                       # Auto-created by START.sh
│
├── frontend/
│   ├── index.html                 # Main UI
│   ├── main.js                    # All frontend logic
│   └── style.css                  # VS Code Dark+ theme + layout
│
├── examples/
│   ├── python_chatbot.py          # Python integration example
│   └── nodejs_chatbot.js          # Node.js integration example
│
├── START.sh                       # One-command setup + start
├── STOP.sh                        # Stop all servers
└── README.md                      # This file
```

---

## 🚀 Quick Reference

```bash
./START.sh                          # setup + start everything
./STOP.sh                           # stop everything

curl http://localhost:8000/healthz  # check backend is alive
tail -f backend.log                 # watch backend logs
tail -f frontend.log                # watch frontend logs

http://localhost:3000               # frontend
http://localhost:8000/docs          # swagger API docs
http://localhost:8000/healthz       # health check
```

---

## 📄 License

MIT — see LICENSE file.

---

**Built with ❤️ for Featherless.ai**
