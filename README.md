# 🚀 H&S Layer - Enhanced AI API

> Transform any LLM into a 10x better AI with skills, tools, and memory

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## ⚡ Quick Start (One Command!)

```bash
./SETUP_FOR_JUDGES.sh
```

**That's it!** This will:
- ✅ Install all dependencies
- ✅ Set up the database
- ✅ Start both servers
- ✅ Open your browser automatically

**Time**: Under 1 minute  
**Manual steps**: ZERO

---

## 🎬 What You'll See

### 1. **Interactive Demo** (Recommended First)
Click **"View Interactive Demo"** to watch a cinematic walkthrough:
- See the complete flow
- Compare raw vs enhanced models
- No setup or API keys needed

### 2. **Live Dashboard**
Click **"Continue with SSO"** to access:
- **A/B Comparison** - Compare raw vs enhanced side-by-side
- **Memory System** - See how it remembers context
- **Skill Store** - 1,080+ specialized skills
- **Tool Builder** - 55+ built-in tools

---

## 🧪 Try These Examples

Once in the dashboard, try:

```
Write a Python calculator
```
**See**: Production-ready code with type hints, docstrings, and syntax highlighting

```
What's the latest version of Python?
```
**See**: Enhanced uses web search tool for current info

```
Calculate 2^10
```
**See**: Enhanced uses math execution tool for precise answer

---

## 📊 Raw vs Enhanced

| Feature | Raw Model | Enhanced Model |
|---------|-----------|----------------|
| **Skills** | ❌ 0 | ✅ 1,080+ |
| **Tools** | ❌ 0 | ✅ 55+ |
| **Memory** | ❌ None | ✅ 3-layer system |
| **Code Quality** | ⚠️ Basic | ✅ Production-ready |
| **Syntax Highlighting** | ❌ Plain text | ✅ VS Code theme |

---

## 🛑 To Stop Servers

```bash
./STOP_SERVERS.sh
```

---

## 📋 System Requirements

- **Python**: 3.8 or higher
- **OS**: macOS, Linux, or Windows
- **RAM**: 2GB minimum
- **Disk**: 500MB free space

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
./STOP_SERVERS.sh
./SETUP_FOR_JUDGES.sh
```

### Python Not Found
Install Python 3.8+ from https://www.python.org/downloads/

---

## ✨ Key Features

- 🎯 **1,080+ Specialized Skills** - Auto-routes to domain experts
- 🛠️ **55+ Built-in Tools** - Web search, code execution, file operations
- 🧠 **Centralized Memory** - Remembers preferences and context
- 💎 **10x Better Code** - Production-ready with proper formatting
- 🔄 **Multi-Provider** - Works with OpenRouter and Featherless
- ⚡ **Intelligent Tool Usage** - Uses tools only when beneficial
- 🎨 **Beautiful UI** - IDE-style syntax highlighting

---

## 🎯 What Makes This Special

### Code Generation Like Claude/GPT-4
- ✅ Type hints on all functions
- ✅ Comprehensive docstrings
- ✅ Proper error handling
- ✅ Clean code structure
- ✅ Syntax highlighting

### Smart Tool Usage
- 🔍 **Web Search** - For current information
- ⚡ **Code Execution** - Test code automatically
- 🧮 **Math Calculations** - Precise results
- 📄 **File Operations** - Read and analyze files

### Memory That Works
- Remembers user preferences
- Recalls previous conversations
- Maintains project context
- Shares knowledge across sessions

---

## 📁 Project Structure

```
H&S_featherless_backend/
├── backend/              # FastAPI backend
│   ├── app/             # Application code
│   │   ├── routes/      # API endpoints
│   │   ├── services/    # Business logic
│   │   ├── models/      # Database models
│   │   └── schemas/     # Pydantic schemas
│   └── requirements.txt # Python dependencies
├── frontend/            # Web interface
│   ├── index.html      # Main HTML
│   ├── main.js         # JavaScript logic
│   └── style.css       # Styles
├── SETUP_FOR_JUDGES.sh # One-command setup
├── START_SERVERS.sh    # Start servers
└── STOP_SERVERS.sh     # Stop servers
```

---

## 🚀 Ready to Start?

```bash
./SETUP_FOR_JUDGES.sh
```

The browser will open automatically at http://localhost:3000

**Enjoy exploring H&S Layer!** 🎉

---

## 📞 Support

If you encounter any issues:
1. Run `./STOP_SERVERS.sh` and try again
2. Check `backend.log` and `frontend.log` for errors
3. Ensure Python 3.8+ is installed

---

## 📄 License

MIT License - See LICENSE file for details

---

**Built with ❤️ for Featherless.ai**
