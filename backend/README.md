# AI Orchestration Backend

FastAPI backend that turns a user-provided LLM API key into a stateful AI agent with skills, memory, and tool execution.

## Product Objective
This backend is not another model provider. It is a middleware layer that sits between a user's app and providers like OpenAI, Anthropic, and OpenRouter.

Flow from your sketch:
- user or website sends a request to your API
- H&S backend runs a small decision model first
- that decision layer picks the skill, memory, and tool path
- the backend then calls the user's main LLM only when needed
- tools, memory, and skills stay centralized in your backend instead of being rebuilt per client

The goal is to reduce token waste, lower cost, improve consistency, and make advanced agent behavior available behind a simple API key workflow.

## Claude-Inspired Skill Design
This backend’s skill system is now modeled after the documented Claude Code skill pattern:
- skills are lazily loaded instructions rather than always-in-context prompts
- skill descriptions drive automatic invocation
- some skills can be manual-only or hidden from direct invocation
- tools are scoped per skill
- a cheaper decision model can choose skills and tools before the main model runs
- workflow skills can run in forked context with isolated memory and stricter tool policies

The main references used for this design were Anthropic’s official Claude Code docs on skills, subagents, memory, hooks, and settings:
- [Skills](https://code.claude.com/docs/en/skills)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [Memory](https://code.claude.com/docs/en/memory)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [Settings](https://code.claude.com/docs/en/settings)

## System Shape
```text
Website / Client App / External API
                |
                v
           H&S Backend
                |
                v
      Small Decision Model
        |      |       |
        v      v       v
      Skills  Memory  Tools
                |
                v
          Main User LLM API
                |
                v
              Response
```

## Included Modules
- Skill engine with trigger matching, versioning, prompt templates, tool permissions, and memory rules.
- Claude-skill compatibility importer for `SKILL.md` skill packs from local folders or git repositories.
- Memory system with:
  - short-term conversation history in PostgreSQL
  - long-term vector retrieval in Chroma with in-memory fallback
  - structured memory metadata in PostgreSQL
- Tool execution layer with `python`, `bash`, `web_search`, `deep_search`, `url_fetch`, `pdf_analyze`, `code_analyze`, and read-only `db_query`
- Orchestration pipeline for `/chat`
- Small decision-model layer for cheaper planning and tool routing
- Encrypted API key storage using a symmetric key derived from `MASTER_KEY`

## Folder Layout
```text
backend/
├── app/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   ├── db/
│   └── utils/
├── requirements.txt
├── .env.example
└── README.md
```

## Quickstart
1. Create and activate a virtual environment.
2. Install dependencies:
```bash
pip install -r backend/requirements.txt
```
3. Copy the environment file:
```bash
cp backend/.env.example backend/.env
```
4. Update at least `DATABASE_URL` and `MASTER_KEY`.
5. Start PostgreSQL.
6. Run the API:
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## Local Test Environment
If you want a simple terminal-only environment where you paste your own key and test the backend directly:

1. Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

2. Create a local test env file:
```bash
cp backend/.env.localtest.example backend/.env
```

3. Generate a valid Fernet key for `MASTER_KEY`:
```bash
.venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

4. Update `DATABASE_URL` in `backend/.env` to point at your local PostgreSQL database.

5. Start the backend:
```bash
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

6. In a second terminal, start the interactive test console:
```bash
.venv/bin/python backend/scripts/backend_test_console.py
```

The console will:
- prompt you for your API key
- save it through `POST /apikey`
- show the current tools and skills
- let you test `/chat`, `/memory`, `/skills`, and `/tools` without any frontend

Default test settings:
- provider: `openrouter`
- model: `openrouter/free`
- memory scope: `workspace`
- context key: `backend-test`

Useful console commands:
- `/chat <prompt>`
- `/skill <name> :: <prompt> :: <arguments?>`
- `/memory <text>`
- `/skills`
- `/tools`
- `/context`
- `/quit`

## Built-In API Simulator
If you want a simple browser demo instead of the terminal console:

1. Start the backend:
```bash
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

2. Open:
```text
http://127.0.0.1:8000/studio
```

The built-in simulator lets you:
- demo the higher-level public API instead of a raw model chat
- choose between `POST /run`, `POST /skills/{skill}`, `POST /tools/{tool}`, and `POST /memory/context`
- show the generated request payload a developer would send
- show an SDK snippet in Python, JavaScript, or curl
- show the orchestrated response alongside the activated skill, tools, and memory context
- present Aurora as an intelligence layer on top of Featherless-style model access

External tool support:
- built-in tools already cover search, deep search, web scraping via `url_fetch`, PDF analysis, code analysis, Python, bash, and DB query
- users can add more tools by registering webhook-backed tools through `POST /tools/external`
- once a tool exists, skills can include that tool name in `tool_permissions`

## Public API
- `POST /run` run the higher-level abstraction API with auto skill routing
- `POST /skills/{skill_name}` run a specific skill through the same orchestration, memory, and tool stack
- `POST /tools/{tool_name}` run a public tool endpoint directly
- `POST /memory` store centralized memory
- `POST /memory/context` fetch reusable centralized context
- `GET /v1/skills` list skill-ready endpoints for the versioned public API layer
- `POST /v1/chat` versioned alias for `/run`
- `POST /v1/run` versioned alias for `/run`
- `POST /v1/skills/{skill_name}` versioned alias for `/skills/{skill_name}`
- `POST /v1/tools/{tool_name}` versioned alias for `/tools/{tool_name}`
- `POST /v1/memory` versioned alias for `/memory`
- `POST /v1/memory/context` versioned alias for `/memory/context`

Example:
```python
import requests

requests.post("http://127.0.0.1:8000/run", json={
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "Review this Python function for bugs",
    "provider": "openrouter",
    "model": "openrouter/free",
    "memory_scope": "workspace",
    "context_key": "demo-project"
})
```

Behind the scenes:
- skill runs explicitly or is auto-selected
- centralized memory is loaded
- tools run when needed
- the chosen upstream LLM is called
- one structured response is returned

## Internal Endpoints
- `POST /apikey` save or rotate an encrypted provider API key
- `POST /skills` create a custom skill
- `POST /skills/import` import Claude-style `SKILL.md` skills from a local path or git repo
- `GET /skills` list built-in and custom skills
- `GET /tools` list available tools and their input contracts
- `POST /tools/run` run a tool directly for testing
- `POST /memory` store structured and vector memory
- `GET /memory` retrieve relevant memories
- `POST /chat` run the orchestration pipeline
- `GET /healthz` health check

## Decision Layer
The backend is designed around two model roles:
- Decision model: cheap model used for planning, routing, and tool selection
- Main model: higher-quality model used for the final answer

By default:
- main model uses `DEFAULT_LLM_MODEL`
- decision model uses `DECISION_LLM_MODEL`

Supported providers:
- `openai`
- `anthropic`
- `openrouter`

This is the main cost-saving mechanism in the architecture.

## Centralized Context Memory
To keep context alive across different model providers and API keys, the backend now supports shared memory buckets:
- `memory_scope`: one of `conversation`, `user`, `workspace`, or `global`
- `context_key`: optional identifier such as a workspace ID, app ID, tenant ID, or project slug

This lets multiple APIs fetch the same context from your backend even when the underlying provider changes.

Recommended pattern:
- use `user` scope for personal cross-provider continuity
- use `workspace` scope with a `context_key` for shared app or team memory
- use `conversation` scope for isolated thread memory
- use `global` scope sparingly for broad defaults or reusable shared context

## Skill Selection
When `skill_name` is not provided on `/chat`, the backend uses the decision model to choose from the available skill catalog based on each skill’s:
- `name`
- `description`
- `when_to_use`
- `tool_permissions`

This mirrors Claude Code’s documented pattern where concise skill descriptions stay available for routing, while full skill instructions are only loaded when the skill is actually invoked.

## Advanced Skill Modes
The skill runtime now supports three invocation modes:
- `auto`: normal skills that can be chosen by the decision model
- `manual`: workflow skills that must be explicitly named by the caller
- `hidden`: background skills that can compose into other skills but are not listed or directly invokable

It also supports two context modes:
- `inline`: normal chat-style execution with recent conversation context
- `fork`: isolated execution that skips short-term chat history and uses only targeted memory retrieval plus explicit skill arguments

This is intended to approximate Claude-style subagent or forked task execution, where a bounded workflow runs with its own smaller context window.

## Workflow Skills And Tool Policies
Built-in workflow skills now include:
- `commit`: manual-only git commit workflow with preapproved `bash` prefixes for `git status`, `git add`, and `git commit`
- `deploy`: manual-only deployment workflow with explicit deployment-oriented shell prefixes
- `issue-fix`: manual-only bugfix workflow with isolated execution context and constrained shell access

Each skill can now declare:
- `argument_hint`: the expected extra arguments for that skill
- `tool_rules`: per-tool allow rules such as approved shell command prefixes
- `context_mode`: whether the skill runs inline or in a forked context

This keeps tool usage deterministic and prevents a workflow skill from using broad shell access by default.

## Tool Runtime
The tool layer now supports a wider provider-agnostic workflow:
- `web_search`: lightweight web search with ranked titles, links, and snippets
- `deep_search`: multi-page search that fetches and consolidates source content
- `url_fetch`: direct page retrieval for source inspection
- `pdf_analyze`: local PDF parsing with metadata and text preview
- `code_analyze`: local file or repository inspection for codebase-aware tasks
- `python`: isolated Python snippets for deterministic transforms
- `bash`: bounded shell execution for workflow skills only
- `db_query`: read-only PostgreSQL access

These tools are designed to reduce repeated prompt stuffing by letting the backend fetch evidence and structured artifacts before the main model call.

## Claude Skill Reuse
Claude Code skills are reusable in this backend with a compatibility layer because the official format is filesystem-based and centered on `SKILL.md` plus optional support files.

What this backend supports:
- importing local skill directories that contain `SKILL.md`
- importing skill repositories over git
- mapping common Claude skill frontmatter such as `name`, `description`, `allowed-tools`, and `disable-model-invocation`
- converting imported skills into your backend skill catalog so they can be selected through `/chat`

What to watch carefully:
- Anthropic’s public skills repo includes both Apache-licensed examples and source-available document skills; review each imported folder before treating it as redistributable product code
- imported skills may reference Claude-specific tools like `Read`, `Grep`, or `WebFetch`; this backend maps the common ones into its own tool layer, but complex skills may still need manual adaptation

This means you do not need to manually author 300 skills in your database. You can build a curated skill marketplace or import pipeline around the existing Claude skill ecosystem.

## Example Requests
Save an API key:
```bash
curl -X POST http://localhost:8000/apikey \
  -H "content-type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "provider": "openai",
    "api_key": "sk-example"
  }'
```

Save an OpenRouter API key:
```bash
curl -X POST http://localhost:8000/apikey \
  -H "content-type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "provider": "openrouter",
    "api_key": "sk-or-v1-..."
  }'
```

List the built-in skills:
```bash
curl http://localhost:8000/skills
```

Create a custom skill:
```bash
curl -X POST http://localhost:8000/skills \
  -H "content-type: application/json" \
  -d '{
    "name": "research",
    "description": "Summarize research-style questions with tool support.",
    "version": "1.0.0",
    "triggers": ["research", "look up", "find"],
    "when_to_use": "Use for external factual lookup and synthesis.",
    "argument_hint": null,
    "prompt_template": "You are the {skill_name} skill. Use memory when helpful. User input: {user_input}\nMemory: {memory_context}",
    "tool_permissions": ["web_search"],
    "invocation_mode": "auto",
    "context_mode": "inline",
    "tool_rules": {},
    "memory_rules": {
      "short_term": true,
      "vector_store": true,
      "structured": true
    }
  }'
```

Import a local Claude-style skill directory:
```bash
curl -X POST http://localhost:8000/skills/import \
  -H "content-type: application/json" \
  -d '{
    "source": "/absolute/path/to/skills",
    "mode": "local",
    "prefix": "market",
    "overwrite": false
  }'
```

Import a git repository of skills:
```bash
curl -X POST http://localhost:8000/skills/import \
  -H "content-type: application/json" \
  -d '{
    "source": "https://github.com/anthropics/skills.git",
    "mode": "git",
    "prefix": "anthropic",
    "overwrite": false
  }'
```

List available tools:
```bash
curl http://localhost:8000/tools
```

Store memory:
```bash
curl -X POST http://localhost:8000/memory \
  -H "content-type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "text": "User prefers concise backend answers.",
    "kind": "preference",
    "memory_scope": "workspace",
    "context_key": "acme-dashboard",
    "metadata": {
      "source": "manual"
    }
  }'
```

Retrieve memory:
```bash
curl "http://localhost:8000/memory?user_id=00000000-0000-0000-0000-000000000001&query=backend&top_k=3&memory_scope=workspace&context_key=acme-dashboard"
```

Fetch centralized context for a different API/provider:
```bash
curl "http://localhost:8000/memory/context?user_id=00000000-0000-0000-0000-000000000001&memory_scope=workspace&context_key=acme-dashboard&query=latest%20user%20preferences"
```

Chat with orchestration:
```bash
curl -X POST http://localhost:8000/chat \
  -H "content-type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "Research the benefits of async FastAPI handlers",
    "provider": "openai",
    "skill_name": "research",
    "memory_scope": "workspace",
    "context_key": "acme-dashboard"
  }'
```

Chat through OpenRouter with a free model:
```bash
curl -X POST http://localhost:8000/chat \
  -H "content-type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "Do deep research on benefits of async FastAPI handlers",
    "provider": "openrouter",
    "model": "openrouter/free",
    "memory_scope": "workspace",
    "context_key": "acme-dashboard"
  }'
```

Run a manual workflow skill with explicit arguments:
```bash
curl -X POST http://localhost:8000/chat \
  -H "content-type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "input": "Prepare the repository commit workflow",
    "provider": "openai",
    "skill_name": "commit",
    "skill_arguments": "feat: centralize cross-provider memory and skill routing",
    "memory_scope": "workspace",
    "context_key": "acme-dashboard"
  }'
```

Built-in skills available by default:
- `default` general fallback assistant
- `summarize` concise summarization
- `research` lookup-oriented answers using `web_search`
- `code_assistant` technical and code help with optional `python`
- `sql_assistant` read-only SQL and database analysis with optional `db_query`
- `debug` root-cause analysis and troubleshooting
- `explain` concept and system explanation
- `review` critical review for bugs and risks
- `planner` execution planning and task breakdown
- `extract` structured data extraction from messy input
- `writer` drafting and rewriting for broad content requests
- `deep_research` source-backed multi-page research
- `pdf_analyst` PDF document inspection and summarization
- `codebase_analyst` repository and code structure analysis
- `commit` manual-only git commit workflow skill
- `deploy` manual-only deployment workflow skill
- `issue-fix` manual-only issue remediation workflow skill

Hidden composed skills available internally:
- `api-orchestration-standards`
- `safe-workflow-rules`

## Deployment
- Suitable for Railway and Render with managed PostgreSQL.
- Set env vars from `backend/.env.example`.
- Put the app behind a process manager in production.
- Replace the mock `web_search` implementation with a real provider before production rollout.
