# 🚀 H&S Layer - Enhanced AI API

> Transform any LLM into a 10x better AI with skills, tools, and memory

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## 📋 Table of Contents

1. [Complete Setup Tutorial](#-complete-setup-tutorial)
2. [What You'll See](#-what-youll-see)
3. [Test Examples](#-test-examples)
4. [Troubleshooting](#-troubleshooting)
5. [Key Features](#-key-features)
6. [Project Structure](#-project-structure)

---

## 🎓 Complete Setup Tutorial

### Step 1: Check System Requirements

Before starting, ensure you have:

- **Python 3.8 or higher** installed
- **Git** installed
- **2GB RAM** minimum
- **500MB disk space** free
- **Internet connection** for dependencies

#### How to Check Python:

**On Mac/Linux:**
```bash
python3 --version
```

**On Windows:**
```bash
python --version
```

**Expected output:** `Python 3.8.x` or higher

#### Don't Have Python?

**Mac:**
```bash
brew install python3
```
Or download from: https://www.python.org/downloads/

**Windows:**
Download from: https://www.python.org/downloads/
- ✅ Check "Add Python to PATH" during installation

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

---

### Step 2: Clone the Repository

Open your terminal and run:

```bash
git clone https://github.com/Safwatsohail/hs-featherless-backend.git
```

**Expected output:**
```
Cloning into 'hs-featherless-backend'...
remote: Enumerating objects: ...
remote: Counting objects: 100% ...
Receiving objects: 100% ...
```

---

### Step 3: Navigate to the Project

```bash
cd hs-featherless-backend
```

**Verify you're in the right place:**
```bash
ls
```

**You should see:**
- `backend/` folder
- `frontend/` folder
- `START.sh` file
- `STOP.sh` file
- `README.md` file

---

### Step 4: Start Everything (One Command!)

```bash
./START.sh
```

**What happens:**

1. **Checks Python** (5 seconds)
   ```
   🔍 Checking Python...
   ✅ Python 3.x found
   ```

2. **Detects your OS** (1 second)
   ```
   💻 OS: Mac/Linux/Windows
   ```

3. **Sets up backend** (20-30 seconds)
   ```
   🔧 Setting up backend...
      Creating virtual environment...
      Activating virtual environment...
      Installing dependencies...
   ✅ Backend ready
   ```

4. **Initializes database** (5 seconds)
   ```
   🗄️  Initializing database...
   ✅ Database ready
   ```

5. **Creates configuration** (2 seconds)
   ```
   ⚙️  Creating .env...
   ✅ Configuration ready
   ```

6. **Starts servers** (5 seconds)
   ```
   🚀 Starting backend...
   ✅ Backend started (PID: 12345)
   🚀 Starting frontend...
   ✅ Frontend started (PID: 12346)
   ```

7. **Opens browser** (automatic)
   ```
   🎉 Ready! Enjoy H&S Layer!
   ```

**Total time:** 30-60 seconds

**Your browser will automatically open to:** http://localhost:3000

---

### Step 5: Choose Your Experience

You'll see two options:

#### Option A: View Interactive Demo (Recommended First)

1. Click **"View Interactive Demo"** button
2. Watch a 9-step cinematic walkthrough
3. See the complete system without any setup
4. Takes 2-3 minutes

**What you'll see:**
- Welcome and introduction
- Simple onboarding flow
- API key bridging
- Dashboard features
- A/B comparison demo
- Code generation quality
- Tool usage examples
- Memory system demo
- Ready to try live

#### Option B: Try Live Dashboard

1. Click **"Continue with SSO"** button
2. Access the full dashboard immediately
3. Try real A/B comparisons
4. Test with live models

---

### Step 6: Test the System

Once in the dashboard, try these examples:

#### Example 1: Code Generation
**Input:**
```
Write a Python calculator
```

**What to observe:**
- **Left pane (Enhanced)**: Production-ready code with type hints, docstrings, syntax highlighting
- **Right pane (Raw)**: Basic code, plain text, no structure

#### Example 2: Research Query
**Input:**
```
What's the latest version of Python?
```

**What to observe:**
- **Enhanced**: Uses web search tool, shows current info
- **Raw**: Generic answer, might be outdated

#### Example 3: Math Calculation
**Input:**
```
Calculate 2^10
```

**What to observe:**
- **Enhanced**: Uses math execution tool, precise answer (1024)
- **Raw**: Text answer, might be wrong

---

### Step 7: Stop the Servers

When you're done testing:

```bash
./STOP.sh
```

**What happens:**
```
🛑 Stopping backend (PID: 12345)...
✅ Backend stopped
🛑 Stopping frontend (PID: 12346)...
✅ Frontend stopped
✅ All servers stopped!
```

---

## 🔧 Troubleshooting

### Problem 1: "Permission denied" when running START.sh

**Solution:**
```bash
chmod +x START.sh STOP.sh
./START.sh
```

---

### Problem 2: "Python not found"

**Symptoms:**
```
❌ Python 3 is not installed!
```

**Solution:**

**Mac:**
```bash
brew install python3
```

**Windows:**
1. Download from https://www.python.org/downloads/
2. Run installer
3. ✅ Check "Add Python to PATH"
4. Restart terminal
5. Try again

**Linux:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

---

### Problem 3: "Port already in use"

**Symptoms:**
```
Error: Address already in use
```

**Solution:**
```bash
./STOP.sh
sleep 2
./START.sh
```

**If that doesn't work:**

**Find and kill process on port 8000:**
```bash
# Mac/Linux
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

**Find and kill process on port 3000:**
```bash
# Mac/Linux
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F
```

---

### Problem 4: "Module not found" errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
cd backend
source .venv/bin/activate  # Mac/Linux
# OR
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
cd ..
./START.sh
```

---

### Problem 5: Browser doesn't open automatically

**Solution:**

Manually open your browser and go to:
```
http://localhost:3000
```

---

### Problem 6: "Database locked" error

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
./STOP.sh
rm backend/ai_orchestrator.db
./START.sh
```

---

### Problem 7: Blank page or "Cannot connect"

**Check if servers are running:**
```bash
# Check backend
curl http://localhost:8000/healthz

# Expected: {"ok":true}
```

**If backend not responding:**
```bash
./STOP.sh
./START.sh
```

**Check logs:**
```bash
tail -f backend.log
tail -f frontend.log
```

---

### Problem 8: "Virtual environment not found"

**Solution:**
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

### Problem 9: Slow installation

**Symptoms:**
Installation takes more than 5 minutes

**Solution:**

**Use faster mirror (Mac/Linux):**
```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt --index-url https://pypi.org/simple
```

**Check internet connection:**
```bash
ping google.com
```

---

### Problem 10: "Command not found: ./START.sh"

**Solution:**

**Make sure you're in the right directory:**
```bash
pwd
# Should show: .../hs-featherless-backend
```

**If not:**
```bash
cd hs-featherless-backend
./START.sh
```

---

## 🎬 What You'll See

### Dashboard Overview

Once started, you'll have access to:

#### 1. **A/B Chat** (Main Feature)
- **Left Pane**: H&S Enhanced
  - 1,080+ skills
  - 55+ tools
  - 3-layer memory
  - Syntax highlighting
  - Production-ready code

- **Right Pane**: Raw Featherless
  - No skills
  - No tools
  - No memory
  - Plain text
  - Basic code

#### 2. **Unified Memory**
- View all stored facts
- Edit or delete memories
- Filter by tags
- Export as JSON

#### 3. **Skill Store**
- 1,080+ specialized skills
- Toggle on/off
- See overhead metrics
- Auto-routing based on query

#### 4. **Tool Builder**
- 55+ built-in tools
- Create custom tools
- Sandboxed execution
- 50ms budget per tool

#### 5. **API Key Management**
- Generate Aurora keys
- Store provider keys
- Test connections
- View usage stats

#### 6. **Developer Docs**
- Complete API reference
- Code examples (cURL, Python, JavaScript, TypeScript)
- Endpoint documentation
- Memory scopes explained

---

## 🧪 Test Examples

### Example 1: Simple Greeting

**Input:**
```
hi
```

**Enhanced Output:**
```
Hello! How can I help you today?
```
- ✅ Short and friendly
- ✅ No unnecessary code

**Raw Output:**
```
Hello
```
- ⚠️ Very basic

---

### Example 2: Code Generation

**Input:**
```
Write a Python calculator
```

**Enhanced Output:**
```python
def calculator(operation: str, a: float, b: float) -> float:
    """
    Perform basic arithmetic operations.
    
    Args:
        operation: Operation type (add/subtract/multiply/divide)
        a: First number
        b: Second number
    
    Returns:
        Result of the operation
    
    Raises:
        ValueError: If operation is invalid or division by zero
    """
    if operation == 'add':
        return a + b
    elif operation == 'subtract':
        return a - b
    elif operation == 'multiply':
        return a * b
    elif operation == 'divide':
        if b == 0:
            raise ValueError('Cannot divide by zero')
        return a / b
    else:
        raise ValueError(f'Invalid operation: {operation}')
```
- ✅ Type hints
- ✅ Comprehensive docstring
- ✅ Error handling
- ✅ Syntax highlighting

**Raw Output:**
```python
def calc(a, b, op):
    if op == 'add':
        return a + b
    elif op == 'sub':
        return a - b
```
- ❌ No type hints
- ❌ No docstring
- ❌ No error handling
- ❌ Plain text

---

### Example 3: Research Query

**Input:**
```
What's the latest version of Python?
```

**Enhanced Output:**
```
*Used: 🔍 Web Search*

The latest stable version of Python is 3.12.1, released on December 7, 2023.
It includes performance improvements, better error messages, and new features...
```
- ✅ Uses web search tool
- ✅ Current information
- ✅ Shows tool usage

**Raw Output:**
```
Python 3.11 is the latest version.
```
- ❌ Outdated information
- ❌ No tool usage

---

### Example 4: Math Calculation

**Input:**
```
Calculate 2^10
```

**Enhanced Output:**
```
*Used: 🧮 Math Calculation*

2^10 = 1024
```
- ✅ Uses math execution tool
- ✅ Precise answer
- ✅ Shows calculation

**Raw Output:**
```
2 to the power of 10 is approximately 1000.
```
- ❌ Wrong answer
- ❌ No tool usage

---

## 📊 Raw vs Enhanced Comparison

| Feature | Raw Model | Enhanced Model |
|---------|-----------|----------------|
| **Skills** | ❌ 0 | ✅ 1,080+ |
| **Tools** | ❌ 0 | ✅ 55+ |
| **Memory** | ❌ None | ✅ 3-layer system |
| **Code Quality** | ⚠️ Basic | ✅ Production-ready |
| **Type Hints** | ❌ No | ✅ Yes |
| **Docstrings** | ❌ No | ✅ Comprehensive |
| **Error Handling** | ❌ No | ✅ Proper try/except |
| **Syntax Highlighting** | ❌ Plain text | ✅ VS Code theme |
| **Temperature** | 🎲 0.9 (random) | 🎯 0.1 (precise) |
| **Tool Usage** | ❌ Never | ✅ When beneficial |
| **Memory Recall** | ❌ Never | ✅ Automatic |
| **Response Time** | ⚡ Fast | ⚡ Fast (+3ms) |

---

## ✨ Key Features

### 1. **1,080+ Specialized Skills**

Skills are automatically selected based on your query:

- **Code queries** → `code_assistant` skill
- **Research queries** → `deep_research` skill
- **Debug queries** → `debug` skill
- **Review queries** → `review` skill
- **Data queries** → `data_analyst` skill

### 2. **55+ Built-in Tools**

Tools are intelligently used when they add value:

- 🔍 **Web Search** - Current information from the internet
- ⚡ **Code Execution** - Run Python/JavaScript code
- 🧮 **Math Calculations** - Precise mathematical results
- 📄 **File Operations** - Read and analyze files
- 🖼️ **Image Analysis** - Analyze images
- 📑 **PDF Analysis** - Extract text from PDFs
- 🗄️ **Database Queries** - SQL execution
- 🌐 **API Calls** - Make HTTP requests

### 3. **3-Layer Memory System**

- **Short-term**: Recent conversation (last 5 messages)
- **Vector Memory**: Semantic search (top 10, score > 0.5)
- **Fact Extraction**: Auto-captures names, preferences, projects, technologies

### 4. **Production-Ready Code**

Every code response includes:
- ✅ Type hints on all functions
- ✅ Comprehensive docstrings (Args, Returns, Raises)
- ✅ Proper error handling (try/except, validation)
- ✅ Clean structure and formatting
- ✅ Syntax highlighting (VS Code Dark+ theme)

### 5. **Multi-Provider Support**

Works with:
- OpenRouter (30,000+ models)
- Featherless (open-source models)

### 6. **Beautiful UI**

- IDE-style syntax highlighting
- Side-by-side A/B comparison
- Real-time streaming responses
- Tool usage indicators
- Memory context display

---

## 📁 Project Structure

```
hs-featherless-backend/
│
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── routes/            # API endpoints
│   │   │   ├── public_api.py  # Main API routes
│   │   │   └── ...
│   │   ├── services/          # Business logic
│   │   │   ├── orchestrator.py # Main orchestration
│   │   │   ├── llm_client.py   # LLM communication
│   │   │   ├── memory_engine.py # Memory management
│   │   │   ├── skill_engine.py  # Skill routing
│   │   │   └── tool_engine.py   # Tool execution
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── core/              # Configuration
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Configuration (auto-created)
│
├── frontend/                  # Web interface
│   ├── index.html            # Main HTML
│   ├── main.js               # JavaScript logic
│   └── style.css             # Styles
│
├── examples/                  # Code examples
│   ├── python_chatbot.py     # Python example
│   └── nodejs_chatbot.js     # Node.js example
│
├── START.sh                   # Start everything
├── STOP.sh                    # Stop servers
├── README.md                  # This file
│
├── backend.log                # Backend logs (auto-created)
├── frontend.log               # Frontend logs (auto-created)
├── .backend.pid               # Backend process ID (auto-created)
└── .frontend.pid              # Frontend process ID (auto-created)
```

---

## 🚀 Quick Reference

### Start the system:
```bash
./START.sh
```

### Stop the system:
```bash
./STOP.sh
```

### Check if running:
```bash
curl http://localhost:8000/healthz
```

### View logs:
```bash
tail -f backend.log
tail -f frontend.log
```

### Access URLs:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

---

## 📞 Support

### If you encounter issues:

1. **Check logs:**
   ```bash
   tail -f backend.log
   tail -f frontend.log
   ```

2. **Restart servers:**
   ```bash
   ./STOP.sh
   ./START.sh
   ```

3. **Check Python version:**
   ```bash
   python3 --version
   ```

4. **Verify ports are free:**
   ```bash
   lsof -i :8000
   lsof -i :3000
   ```

5. **Reinstall dependencies:**
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

## 📄 License

MIT License - See LICENSE file for details

---

## 🎉 Ready to Start?

```bash
git clone https://github.com/Safwatsohail/hs-featherless-backend.git
cd hs-featherless-backend
./START.sh
```

**That's it!** Your browser will open automatically.

**Enjoy exploring H&S Layer!** 🚀

---

**Built with ❤️ for Featherless.ai**
