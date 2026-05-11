from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.schemas.chat import ToolCall
from app.services.api_key_service import ApiKeyService
from app.services.llm_client import LLMClient, LLMError
from app.services.memory_engine import MemoryEngine
from app.services.skill_engine import SkillEngine
from app.services.tool_engine import ToolEngine, ToolError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrchestratorResult:
    conversation_id: uuid.UUID
    skill: str
    tool_calls: list[ToolCall]
    tool_results: list[dict]
    provider: str
    model: str
    output: str
    memory_hits: int
    short_context_messages: int
    usage: dict


class Orchestrator:
    assistant_memory_max_chars = 500
    openrouter_legacy_model_aliases = {
        "meta-llama/llama-3.3-8b-instruct:free": "openrouter/free",
        "deep-seek": "openrouter/free",
        "deepseek": "openrouter/free",
        "deep seek": "openrouter/free",
        "deepseek/free": "openrouter/free",
    }

    def __init__(
        self,
        *,
        db: AsyncSession,
        api_keys: ApiKeyService,
        skills: SkillEngine,
        memory: MemoryEngine,
        tools: ToolEngine,
        llm_base_urls: dict[str, str],
        default_provider: str,
        default_model: str,
        vector_top_k: int,
    ) -> None:
        self.db = db
        self.api_keys = api_keys
        self.skills = skills
        self.memory = memory
        self.tools = tools
        self.llm_base_urls = llm_base_urls
        self.default_provider = default_provider
        self.default_model = default_model
        self.vector_top_k = vector_top_k

    async def process_request(
        self,
        *,
        user_id: uuid.UUID,
        user_input: str,
        conversation_id: uuid.UUID | None,
        provider: str | None,
        model: str | None,
        skill_name: str | None = None,
        skill_arguments: str | None = None,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> OrchestratorResult:
        await self.api_keys.ensure_user(user_id)
        await self.skills.ensure_builtin_skills()

        selected_provider = provider or self.default_provider
        selected_model = self._normalize_model(
            provider=selected_provider,
            model=model or self.default_model,
        )
        api_key = await self.api_keys.get_decrypted_key(user_id=user_id, provider=selected_provider)
        if not api_key:
            raise LLMError(
                f"No API key stored for provider={selected_provider}. Save one via POST /apikey first."
            )

        llm = LLMClient(
            provider=selected_provider,
            api_key=api_key,
            base_url=self._get_base_url(selected_provider),
        )
        planner_provider = self._resolve_decision_provider(selected_provider)
        planner_model = self._resolve_decision_model(selected_model)
        planner_api_key = api_key
        if planner_provider != selected_provider:
            planner_api_key = await self.api_keys.get_decrypted_key(user_id=user_id, provider=planner_provider)
            if not planner_api_key:
                planner_provider = selected_provider
                planner_api_key = api_key

        planner_llm = LLMClient(
            provider=planner_provider,
            api_key=planner_api_key,
            base_url=self._get_base_url(planner_provider),
        )

        skill = await self._select_skill(
            user_input=user_input,
            skill_name=skill_name,
            planner_llm=planner_llm,
            planner_model=planner_model,
        )
        skill_config = self.skills.get_skill_config(skill)
        skill_config["active_arguments"] = skill_arguments or ""
        if skill_config.get("invocation_mode") == "manual" and skill_config.get("argument_hint") and not skill_arguments:
            raise ValueError(
                f"Skill '{skill.name}' requires skill_arguments. Expected: {skill_config['argument_hint']}"
            )
        prompt_template = await self.skills.expand_composed_prompts(skill)

        conv = await self._get_or_create_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
            title=None,
            memory_scope=memory_scope,
            context_key=context_key,
        )

        short_msgs: list[Message] = []
        vector_hits: list[dict] = []
        if skill_config.get("context_mode") != "fork":
            short_msgs = await self.memory.short_term(conversation_id=conv.id, user_id=user_id)
        vector_hits = await self.memory.vector_retrieve(
            user_id=user_id,
            query=user_input if skill_config.get("context_mode") != "fork" else (skill_arguments or user_input),
            top_k=self.vector_top_k,
            memory_scope=memory_scope,
            context_key=context_key,
        )
        memory_context = self._format_memory_context(vector_hits)
        rendered_prompt = prompt_template.format(
            user_input=user_input,
            memory_context=memory_context,
            skill_name=skill.name,
            tool_permissions=", ".join(skill.tool_permissions or []) or "none",
            skill_arguments=skill_arguments or "",
        )

        system_prompt = self._build_system_prompt(
            rendered_prompt,
            short_msgs,
            vector_hits,
            context_mode=skill_config.get("context_mode", "inline"),
        )
        user_message = user_input
        if skill_arguments:
            user_message = f"{user_input}\n\nSkill arguments:\n{skill_arguments}"
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]

        if skill_config.get("preferred_model"):
            selected_model = skill_config["preferred_model"]

        tool_calls: list[ToolCall] = []
        tool_outputs: list[dict] = []
        permitted_tools = list(skill.tool_permissions or [])
        
        # AGGRESSIVE TOOL USAGE - Always try to use tools when available
        if permitted_tools:
            # First try intelligent fallback (works better than LLM planning)
            tool_calls = self._fallback_tool_calls(
                skill_name=skill.name,
                user_input=user_input,
                skill_arguments=skill_arguments,
                permitted_tools=permitted_tools,
            )
            
            # If no tools selected, try LLM planning as backup
            if not tool_calls:
                planner_tools = await self.tools.get_tool_specs(permitted_tools)
                plan = await planner_llm.plan_tool_calls(model=planner_model, messages=messages, tools=planner_tools)
                for call in plan.get("tool_calls", []):
                    try:
                        tc = ToolCall.model_validate(call)
                    except Exception:  # noqa: BLE001
                        continue
                    if tc.name not in permitted_tools:
                        continue
                    if not self._is_tool_call_allowed(skill_config=skill_config, tool_call=tc):
                        continue
                    tool_calls.append(tc)

        for tc in tool_calls:
            try:
                result = await self.tools.execute_tool(tc.name, tc.input)
                tool_outputs.append(
                    {"name": result.name, "output": result.output, "metadata": result.metadata}
                )
            except ToolError as exc:
                tool_outputs.append({"name": tc.name, "output": f"ToolError: {exc}", "metadata": {}})

        if tool_outputs:
            # Format tool results in a user-friendly way (like Claude shows tool usage)
            tool_summary = []
            for tool_out in tool_outputs:
                tool_name = tool_out.get("name", "unknown")
                tool_output = tool_out.get("output", "")
                
                # Create a clean summary
                if tool_name == "web_search":
                    tool_summary.append(f"🔍 Searched the web")
                elif tool_name == "deep_search":
                    tool_summary.append(f"🔬 Performed deep research")
                elif tool_name == "code_exec":
                    tool_summary.append(f"⚡ Executed code")
                elif tool_name == "math_exec":
                    tool_summary.append(f"🧮 Calculated result")
                elif tool_name == "file_read":
                    tool_summary.append(f"📄 Read file")
                elif tool_name == "image_analyze":
                    tool_summary.append(f"🖼️ Analyzed image")
                elif tool_name == "pdf_analyze":
                    tool_summary.append(f"📑 Analyzed PDF")
                elif tool_name == "sql_exec":
                    tool_summary.append(f"🗄️ Queried database")
                elif tool_name == "api_call":
                    tool_summary.append(f"🌐 Called API")
                else:
                    tool_summary.append(f"🔧 Used {tool_name}")
            
            # Inject tool results with a clean header
            tool_header = "\n".join(tool_summary)
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Tool Results:\n{tool_header}\n\n"
                        f"Raw Data:\n{json.dumps(tool_outputs, ensure_ascii=False)}\n\n"
                        f"Use these results to provide a comprehensive answer. "
                        f"Integrate the data naturally into your response."
                    ),
                }
            )

        is_code_request = self._is_code_generation_request(user_input)
        temperature = 0.1 if is_code_request else 0.2
        if not is_code_request and any(keyword in user_input.lower() for keyword in ['brainstorm', 'creative', 'story', 'idea', 'imagine']):
            temperature = 0.7
        
        final = await llm.generate(model=selected_model, messages=messages, temperature=temperature)
        output_text = self._cleanup_model_output(final.content, user_input=user_input)
        
        if tool_outputs:
            tool_header_parts = []
            for tool_out in tool_outputs:
                tool_name = tool_out.get("name", "unknown")
                if tool_name == "web_search":
                    tool_header_parts.append("🔍 Web Search")
                elif tool_name == "deep_search":
                    tool_header_parts.append("🔬 Deep Research")
                elif tool_name == "code_exec":
                    tool_header_parts.append("⚡ Code Execution")
                elif tool_name == "math_exec":
                    tool_header_parts.append("🧮 Math Calculation")
                elif tool_name == "file_read":
                    tool_header_parts.append("📄 File Read")
                elif tool_name == "image_analyze":
                    tool_header_parts.append("🖼️ Image Analysis")
                elif tool_name == "pdf_analyze":
                    tool_header_parts.append("📑 PDF Analysis")
                elif tool_name == "sql_exec":
                    tool_header_parts.append("🗄️ Database Query")
                elif tool_name == "api_call":
                    tool_header_parts.append("🌐 API Call")
                else:
                    tool_header_parts.append(f"🔧 {tool_name.replace('_', ' ').title()}")
            
            if tool_header_parts:
                tool_header = " • ".join(tool_header_parts)
                output_text = f"*Used: {tool_header}*\n\n{output_text}"

        await self._store_turn(
            user_id=user_id,
            conversation_id=conv.id,
            user_input=user_input,
            assistant_output=output_text,
            tool_calls=tool_calls,
            tool_outputs=tool_outputs,
            skill_name=skill.name,
            provider=selected_provider,
            model=selected_model,
            memory_scope=memory_scope,
            context_key=context_key,
        )

        return OrchestratorResult(
            conversation_id=conv.id,
            skill=skill.name,
            tool_calls=tool_calls,
            tool_results=tool_outputs,
            provider=selected_provider,
            model=selected_model,
            output=output_text,
            memory_hits=len(vector_hits),
            short_context_messages=len(short_msgs),
            usage=final.raw.get("usage") or {},
        )

    async def _get_or_create_conversation(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        title: str | None,
        memory_scope: str,
        context_key: str | None,
    ) -> Conversation:
        uid_str = str(user_id)
        if conversation_id:
            res = await self.db.execute(select(Conversation).where(Conversation.id == str(conversation_id)))
            conv = res.scalar_one_or_none()
            if conv and conv.user_id == uid_str:
                return conv

        conv = Conversation(user_id=uid_str, title=title, memory_scope=memory_scope, context_key=context_key)
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    def _build_system_prompt(
        self,
        skill_template: str,
        short_msgs: list[Message],
        vector_hits: list[dict],
        *,
        context_mode: str,
    ) -> str:
        parts = [skill_template.strip(), "\n\n"]
        if context_mode == "fork":
            parts.append(
                "Execution context: isolated forked skill context. Do not assume prior chat history beyond attached memory.\n\n"
            )
        
        # Add memory context if available
        if vector_hits:
            parts.append("=== MEMORY CONTEXT (use this to personalize your response) ===\n")
            for hit in vector_hits[:5]:  # Top 5 most relevant memories
                text = hit.get("text", "")
                score = hit.get("score", 0)
                if text and score > 0.5:  # Only include relevant memories
                    parts.append(f"• {text}\n")
            parts.append("\n")
        
        if short_msgs:
            parts.append("=== RECENT CONVERSATION ===\n")
            for m in short_msgs[-5:]:  # Last 5 messages for context
                parts.append(f"{m.role}: {m.content[:200]}\n")
            parts.append("\n")
        
        parts.append(
            "\n=== YOUR ENHANCED CAPABILITIES ===\n"
            "You have access to powerful tools and skills that make you superior to basic AI models:\n\n"
            
            "🔧 TOOLS (55+ available):\n"
            "- Code execution (Python, JavaScript, etc.)\n"
            "- Web search and deep research\n"
            "- File operations and analysis\n"
            "- Mathematical calculations\n"
            "- Image and PDF analysis\n"
            "- API calls and database queries\n"
            "USE TOOLS when they add value to your response!\n\n"
            
            "🎯 SKILLS (1,080+ available):\n"
            "- Automatically selected based on query type\n"
            "- Code assistant, research, debugging, review, data analysis\n"
            "- Each skill has specialized prompts and tool permissions\n"
            "Your current skill has been optimized for this query!\n\n"
            
            "🧠 MEMORY:\n"
            "- Remember user preferences, projects, and context\n"
            "- Access conversation history\n"
            "- Personalize responses based on past interactions\n\n"
            
            "\n=== RESPONSE EXCELLENCE GUIDELINES ===\n"
            "You are an ELITE AI assistant with enhanced capabilities.\n\n"
            
            "🎯 RESPONSE MATCHING:\n"
            "Match your response style to the query complexity:\n\n"
            
            "SIMPLE QUERIES (greetings, thanks, yes/no):\n"
            "- 1-2 sentences maximum\n"
            "- Warm and friendly\n"
            "- NO code examples\n"
            "- NO lengthy explanations\n"
            "- Example: 'Hi! How can I help you today?'\n\n"
            
            "COMPLEX QUERIES (code, explanations, analysis):\n"
            "- Comprehensive and detailed\n"
            "- Use headers and structure\n"
            "- Include code examples when relevant\n"
            "- Provide specific details\n\n"
            
            "🔥 CODE GENERATION (Like Claude/GPT-4):\n"
            "When user requests code, generate PRODUCTION-READY code with PERFECT structure:\n\n"
            
            "📋 MANDATORY STRUCTURE:\n"
            "1. ONE brief intro sentence (what the code does)\n"
            "2. ONE code block with ONLY executable code\n"
            "3. ONE brief usage note (if needed)\n"
            "4. NO extra snippets, NO multiple versions, NO alternatives\n\n"
            
            "✅ PERFECT EXAMPLE (Python calculator):\n\n"
            "Here's a production-ready calculator:\n\n"
            "```python\n"
            "def calculator(operation: str, a: float, b: float) -> float:\n"
            "    \"\"\"\n"
            "    Perform basic arithmetic operations.\n"
            "    \n"
            "    Args:\n"
            "        operation: Operation type (add/subtract/multiply/divide)\n"
            "        a: First number\n"
            "        b: Second number\n"
            "    \n"
            "    Returns:\n"
            "        Result of the operation\n"
            "    \n"
            "    Raises:\n"
            "        ValueError: If operation is invalid or division by zero\n"
            "    \"\"\"\n"
            "    if operation == 'add':\n"
            "        return a + b\n"
            "    elif operation == 'subtract':\n"
            "        return a - b\n"
            "    elif operation == 'multiply':\n"
            "        return a * b\n"
            "    elif operation == 'divide':\n"
            "        if b == 0:\n"
            "            raise ValueError('Cannot divide by zero')\n"
            "        return a / b\n"
            "    else:\n"
            "        raise ValueError(f'Invalid operation: {operation}')\n"
            "```\n\n"
            "Call with `calculator('add', 5, 3)` to get 8.\n\n"
            
            "🚫 NEVER DO THIS:\n"
            "❌ Multiple code blocks for same task\n"
            "❌ Explanatory comments inside code (except docstrings)\n"
            "❌ Missing type hints\n"
            "❌ Incomplete error handling\n"
            "❌ Code mixed with explanatory text\n"
            "❌ Alternative versions or 'you could also...'\n\n"
            
            "✅ CODE EXCELLENCE RULES:\n"
            "- ONE code block per request (unless explicitly asked for multiple)\n"
            "- Code blocks contain ONLY executable code\n"
            "- ALWAYS use type hints (Python: int, str, float, list, dict, etc.)\n"
            "- ALWAYS include comprehensive docstrings\n"
            "- ALWAYS handle errors properly (try/except, raise, validation)\n"
            "- NO explanatory comments (docstring is enough)\n"
            "- NO inline explanations like '# This does X'\n"
            "- Explanation goes BEFORE code (1 sentence) or AFTER code (usage)\n"
            "- Use correct language tag: ```python, ```javascript, ```typescript, etc.\n"
            "- Match user's preferred language (Python by default)\n\n"
            
            "🎯 LANGUAGE DETECTION:\n"
            "- User says 'Python' → ```python\n"
            "- User says 'JavaScript' → ```javascript\n"
            "- User says 'TypeScript' → ```typescript\n"
            "- User says 'Java' → ```java\n"
            "- User says 'C++' → ```cpp\n"
            "- No language specified → ```python (default)\n\n"
            
            "💬 CONVERSATION EXAMPLES:\n\n"
            "Query: 'hi'\n"
            "Response: 'Hello! How can I help you today?'\n\n"
            
            "Query: 'thanks'\n"
            "Response: 'You're welcome! Let me know if you need anything else.'\n\n"
            
            "Query: 'what can you do?'\n"
            "Response: 'I can help with coding, explanations, analysis, and more. I have access to 1,080+ skills, 55+ tools, and remember our conversations. What would you like help with?'\n\n"
            
            "Query: 'Write a Python function to add two numbers'\n"
            "Response: [Full code with type hints and docstring]\n\n"
            
            "🚨 CRITICAL RULES (NEVER BREAK THESE):\n"
            "- NO code for greetings or simple queries\n"
            "- NO meta-commentary ('As an AI...', 'I'm just a model...')\n"
            "- NO HTML tags in responses\n"
            "- NO overly verbose responses for simple questions\n"
            "- NO multiple code snippets for same task (ONE perfect solution)\n"
            "- NO alternative versions unless explicitly asked\n"
            "- NO explanatory comments inside code (docstrings only)\n"
            "- CODE BLOCKS CONTAIN ONLY CODE - explanations go outside\n"
            "- NEVER mix explanatory text inside code blocks\n"
            "- Match response length to query complexity\n"
            "- Be EFFICIENT and PRECISE like Claude/GPT-4\n\n"
            
            "✅ ALWAYS DO:\n"
            "- Be warm and friendly\n"
            "- Use memory when available\n"
            "- Provide value in every response\n"
            "- Keep simple queries simple (1-2 sentences)\n"
            "- Make code queries PERFECT (production-ready, type hints, docstrings)\n"
            "- Use correct language tag in code blocks\n"
            "- Separate explanation from code (before/after, never inside)\n"
            "- Generate ONE perfect solution, not multiple alternatives\n"
            "- Use tools when they add value (code_exec, web_search, etc.)\n"
        )
        return "".join(parts).strip()

    def _normalize_model(self, *, provider: str, model: str) -> str:
        if provider == "openrouter":
            normalized = model.strip().lower()
            return self.openrouter_legacy_model_aliases.get(normalized, model)
        return model

    @staticmethod
    def _format_memory_context(vector_hits: list[dict]) -> str:
        if not vector_hits:
            return "No relevant memories."
        return "\n".join(str(hit.get("text") or "")[:800] for hit in vector_hits)

    @staticmethod
    def _is_code_generation_request(user_input: str) -> bool:
        normalized = user_input.lower()
        return any(
            keyword in normalized
            for keyword in [
                "write", "create", "generate", "code", "function", "script",
                "program", "class", "implement", "build", "python", "javascript",
                "typescript", "java", "c++", "rust", "go", "calculator",
            ]
        )

    def _cleanup_model_output(self, content: str, *, user_input: str) -> str:
        output_text = content.strip().strip('"').strip("'").strip()
        for pattern in [
            "Here's my response to the given prompt:",
            "I'm just a text-based model and don't have the ability to",
            "I can only respond based on the user prompt given to me.",
            "As an AI language model,",
            "As an AI assistant,",
            "I apologize, but",
            "I'm sorry, but",
        ]:
            output_text = "\n".join(
                line for line in output_text.splitlines() if pattern not in line
            ).strip()

        output_text = re.sub(r'class="[^"]*"', "", output_text)
        output_text = re.sub(r"<(?!/?(?:br|p|ul|ol|li)\b)[^>]+>", "", output_text)
        output_text = re.sub(r"\n{4,}", "\n\n\n", output_text).strip()

        if self._is_code_generation_request(user_input):
            output_text = self._normalize_code_response(output_text, user_input=user_input)
        elif output_text.count("```") % 2 != 0:
            output_text += "\n```"

        return output_text

    def _normalize_code_response(self, output_text: str, *, user_input: str) -> str:
        lang = self._detect_code_language(user_input, output_text)
        output_text = re.sub(r"(?m)^`{3,}\s*([A-Za-z0-9_+#.-]+)?\s*$", lambda m: f"```{m.group(1) or ''}".rstrip(), output_text)

        blocks = list(re.finditer(r"```([A-Za-z0-9_+#.-]*)\n([\s\S]*?)```", output_text))
        if blocks:
            seen: set[str] = set()
            rebuilt = []
            last = 0
            for block in blocks:
                block_lang = block.group(1).strip() or lang
                code = self._normalize_code_block(block.group(2), block_lang)
                normalized_code = re.sub(r"\s+", "", code)
                rebuilt.append(output_text[last:block.start()])
                if normalized_code not in seen:
                    rebuilt.append(f"```{block_lang}\n{code}\n```")
                    seen.add(normalized_code)
                last = block.end()
            rebuilt.append(output_text[last:])
            return re.sub(r"\n{4,}", "\n\n\n", "".join(rebuilt)).strip()

        if self._looks_like_standalone_code(output_text):
            return f"```{lang}\n{self._normalize_code_block(output_text, lang)}\n```"

        return output_text

    @staticmethod
    def _normalize_code_block(code: str, language: str) -> str:
        code = code.replace("\r\n", "\n").replace("\r", "\n").strip()
        code = re.sub(r"`\s*\n\s*([A-Za-z_][A-Za-z0-9_]*)\s*\n", r"\1", code)
        code = re.sub(r"\n\s*([A-Za-z_][A-Za-z0-9_]*)\s*\n(?=[.,;:])", r" \1", code)
        code = re.sub(r"(?<=\w) {2,}(?=\w)", " ", code)
        code = re.sub(r"(?m)^([ \t]*)`([^`\n]+)`$", r"\1\2", code)
        code = re.sub(r"\n{3,}", "\n\n", code)
        if language.lower() not in {"python", "py"}:
            return code

        lines = [line.rstrip() for line in code.replace("\t", "    ").split("\n")]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        normalized: list[str] = []
        in_docstring = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                normalized.append("")
                continue

            leading = len(line) - len(line.lstrip(" "))
            if leading:
                leading = max(4, ((leading + 3) // 4) * 4)

            if stripped.startswith(('"""', "'''")):
                in_docstring = not (stripped.count('"""') == 2 or stripped.count("'''") == 2)
            elif in_docstring and stripped.endswith(('"""', "'''")):
                in_docstring = False

            normalized.append((" " * leading) + stripped)

        return "\n".join(normalized)

    @staticmethod
    def _detect_code_language(user_input: str, output_text: str) -> str:
        combined = f"{user_input}\n{output_text}".lower()
        if "typescript" in combined or re.search(r"\binterface\s+\w+|:\s*(string|number|boolean)\b", output_text):
            return "typescript"
        if "javascript" in combined or re.search(r"\b(const|let|function)\s+\w+|=>", output_text):
            return "javascript"
        if "bash" in combined or "shell" in combined:
            return "bash"
        if "java" in combined and "javascript" not in combined:
            return "java"
        if "c++" in combined or "cpp" in combined:
            return "cpp"
        if "go " in combined or "golang" in combined:
            return "go"
        if "rust" in combined:
            return "rust"
        return "python"

    @staticmethod
    def _looks_like_standalone_code(output_text: str) -> bool:
        lines = [line for line in output_text.strip().splitlines() if line.strip()]
        if not lines:
            return False
        codeish = sum(
            1
            for line in lines
            if re.match(r"\s*(def |class |import |from |async def |@|const |let |function |export |interface |type |public |private )", line)
            or line.startswith(("    ", "\t", "}", "});"))
        )
        return codeish / len(lines) >= 0.55

    def _is_tool_call_allowed(self, *, skill_config: dict, tool_call: ToolCall) -> bool:
        tool_rules = skill_config.get("tool_rules") or {}
        rule = tool_rules.get(tool_call.name)
        if not rule:
            return True
        if tool_call.name == "bash":
            command = str(tool_call.input.get("command") or "").strip()
            prefixes = rule.get("command_prefixes") or []
            return any(command.startswith(prefix) for prefix in prefixes)
        return True

    def _fallback_tool_calls(
        self,
        *,
        skill_name: str,
        user_input: str,
        skill_arguments: str | None,
        permitted_tools: list[str],
    ) -> list[ToolCall]:
        """
        SMART tool selection - only use tools when they're actually needed.
        Don't use tools for simple greetings or general conversation.
        """
        normalized = f"{user_input}\n{skill_arguments or ''}".lower()
        tool_set = set(permitted_tools)
        calls: list[ToolCall] = []

        # Skip tools for simple greetings and general conversation
        simple_patterns = [
            "hi", "hello", "hey", "greetings", "good morning", "good afternoon",
            "how are you", "what's up", "sup", "yo", "thanks", "thank you",
            "bye", "goodbye", "see you", "ok", "okay", "yes", "no"
        ]
        if any(normalized.strip() == pattern for pattern in simple_patterns):
            return []  # No tools for simple greetings
        
        # Skip tools if query is too short and not code-related
        if len(user_input.strip()) < 15 and not any(kw in normalized for kw in ["code", "function", "class", "script"]):
            return []

        # PDF Analysis - highest priority for PDF files
        if "pdf_analyze" in tool_set and ".pdf" in normalized:
            pdf_path = self._extract_local_path(normalized_source=user_input + "\n" + (skill_arguments or ""), suffix=".pdf")
            if pdf_path:
                calls.append(ToolCall(name="pdf_analyze", input={"path": pdf_path}))
                return calls

        # Deep Research - for comprehensive research queries
        if "deep_search" in tool_set and (
            skill_name == "deep_research"
            or any(term in normalized for term in [
                "deep research", "research paper", "comprehensive analysis",
                "detailed study", "investigate thoroughly"
            ])
        ):
            calls.append(ToolCall(name="deep_search", input={"query": user_input}))
            return calls

        # Web Search - ONLY for information lookup queries
        if "web_search" in tool_set and any(
            term in normalized for term in [
                "latest", "current", "news", "recent update",
                "what is the latest", "what are the new", "release date",
                "price of", "cost of", "available in", "when was",
                "who is", "where is", "search for", "look up",
                "find information about", "tell me about the latest"
            ]
        ):
            calls.append(ToolCall(name="web_search", input={"query": user_input}))
            return calls

        # Code Execution - ONLY when user explicitly wants to run code
        if "code_exec" in tool_set and any(
            term in normalized for term in [
                "run this code", "execute this", "test this code",
                "what does this code do", "debug this", "run the following"
            ]
        ):
            if "```" in user_input:
                calls.append(ToolCall(name="code_exec", input={"code": user_input}))
                return calls

        # Math Execution - ONLY for explicit calculations
        if "math_exec" in tool_set and any(
            term in normalized for term in [
                "calculate", "compute", "what is", "solve",
                "math problem", "equation"
            ]
        ) and any(char in user_input for char in ["+", "-", "*", "/", "=", "^"]):
            calls.append(ToolCall(name="math_exec", input={"expression": user_input}))
            return calls

        # File Operations - ONLY when file path is mentioned
        if "file_read" in tool_set and any(
            term in normalized for term in ["read file", "open file", "show file", "content of file"]
        ):
            import re
            file_match = re.search(r'["\']([^"\']+\.[a-z]{2,4})["\']', user_input)
            if file_match:
                calls.append(ToolCall(name="file_read", input={"path": file_match.group(1)}))
                return calls

        # Image Analysis - ONLY when image is mentioned
        if "image_analyze" in tool_set and any(
            term in normalized for term in ["analyze image", "what's in this image", "describe image"]
        ):
            import re
            img_match = re.search(r'["\']([^"\']+\.(?:jpg|jpeg|png|gif|webp))["\']', user_input, re.IGNORECASE)
            if img_match:
                calls.append(ToolCall(name="image_analyze", input={"path": img_match.group(1)}))
                return calls

        # Code Analysis - ONLY for explicit codebase questions
        if "code_analyze" in tool_set and (
            skill_name in {"codebase_analyst", "code_review"}
            or any(term in normalized for term in [
                "analyze codebase", "review code", "inspect repository",
                "code structure", "project structure", "codebase overview"
            ])
        ):
            code_path = self._extract_local_path(
                normalized_source=user_input + "\n" + (skill_arguments or ""),
                suffix=None,
            ) or "."
            calls.append(ToolCall(name="code_analyze", input={"path": code_path, "query": user_input}))
            return calls

        # Default: NO TOOLS for general conversation
        return []

    @staticmethod
    def _extract_local_path(*, normalized_source: str, suffix: str | None) -> str | None:
        for token in normalized_source.replace("\n", " ").split():
            candidate = token.strip(" ,\"'`()[]")
            if "/" not in candidate and not candidate.startswith("."):
                continue
            if suffix and not candidate.lower().endswith(suffix):
                continue
            return candidate
        return None

    async def _store_turn(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_input: str,
        assistant_output: str,
        tool_calls: list[ToolCall],
        tool_outputs: list[dict],
        skill_name: str,
        provider: str,
        model: str,
        memory_scope: str,
        context_key: str | None,
    ) -> None:
        self.db.add(
            Message(conversation_id=str(conversation_id), user_id=str(user_id), role="user", content=user_input)
        )
        self.db.add(
            Message(
                conversation_id=str(conversation_id), user_id=str(user_id), role="assistant", content=assistant_output
            )
        )
        await self.db.commit()

        await self.memory.vector_store_text(
            user_id=user_id,
            conversation_id=conversation_id,
            text=user_input,
            memory_scope=memory_scope,
            context_key=context_key,
            metadata={"role": "user"},
        )
        
        # Extract and store facts from user input
        await self._extract_and_store_facts(
            user_id=user_id,
            conversation_id=conversation_id,
            text=user_input,
            memory_scope=memory_scope,
            context_key=context_key
        )
        
        assistant_memory_text = self._compress_assistant_memory(assistant_output)
        if assistant_memory_text:
            await self.memory.vector_store_text(
                user_id=user_id,
                conversation_id=conversation_id,
                text=assistant_memory_text,
                memory_scope=memory_scope,
                context_key=context_key,
                metadata={"role": "assistant_summary"},
            )
        await self.memory.store_structured(
            user_id=user_id,
            conversation_id=conversation_id,
            kind="turn",
            memory_scope=memory_scope,
            context_key=context_key,
            data={
                "user_input": user_input,
                "assistant_output": assistant_output,
                "skill": skill_name,
                "provider": provider,
                "model": model,
                "tool_count": len(tool_calls),
            },
        )
        if tool_calls:
            await self.memory.store_structured(
                user_id=user_id,
                conversation_id=conversation_id,
                kind="tool_calls",
                memory_scope=memory_scope,
                context_key=context_key,
                data={"tool_calls": [tc.model_dump() for tc in tool_calls], "tool_outputs": tool_outputs},
            )

    def _get_base_url(self, provider: str) -> str:
        try:
            return self.llm_base_urls[provider]
        except KeyError as exc:
            raise ValueError(f"Unsupported provider '{provider}'.") from exc

    def _compress_assistant_memory(self, assistant_output: str) -> str | None:
        text = assistant_output.strip()
        if not text:
            return None
        if "Tool results:" in text:
            text = text.split("Tool results:", 1)[0].strip()
        text = text[: self.assistant_memory_max_chars].strip()
        if len(text) < 40:
            return None
        return text

    def _resolve_decision_provider(self, selected_provider: str) -> str:
        return self.skills.session.info.get("decision_llm_provider") or selected_provider

    def _resolve_decision_model(self, selected_model: str) -> str:
        return self.skills.session.info.get("decision_llm_model") or selected_model

    async def _select_skill(
        self,
        *,
        user_input: str,
        skill_name: str | None,
        planner_llm: LLMClient,
        planner_model: str,
    ):
        if skill_name:
            return await self.skills.select_skill(user_input=user_input, skill_name=skill_name)

        # SMART SKILL ROUTING - Like Claude's automatic skill selection
        normalized = user_input.lower()
        
        # Code-related queries → code_assistant
        if any(kw in normalized for kw in [
            "write", "create", "generate", "code", "function", "class", "script",
            "program", "implement", "build", "develop", "python", "javascript",
            "typescript", "java", "c++", "rust", "go", "ruby", "php", "calculator",
            "algorithm", "data structure", "api", "backend", "frontend"
        ]):
            code_skill = await self.skills.get_by_name("code_assistant")
            if code_skill:
                return code_skill
        
        # Research queries → deep_research
        if any(kw in normalized for kw in [
            "research", "analyze", "compare", "investigate", "study",
            "latest", "current", "what are the", "tell me about", "explain"
        ]):
            research_skill = await self.skills.get_by_name("deep_research")
            if research_skill:
                return research_skill
        
        # Data/analytics queries → data_analyst
        if any(kw in normalized for kw in [
            "analyze data", "statistics", "metrics", "dashboard", "report",
            "visualization", "chart", "graph", "sql", "database"
        ]):
            data_skill = await self.skills.get_by_name("data_analyst")
            if data_skill:
                return data_skill
        
        # Debugging queries → debug
        if any(kw in normalized for kw in [
            "debug", "fix", "error", "bug", "issue", "problem", "not working",
            "broken", "crash", "exception", "traceback"
        ]):
            debug_skill = await self.skills.get_by_name("debug")
            if debug_skill:
                return debug_skill
        
        # Code review queries → review
        if any(kw in normalized for kw in [
            "review", "check", "improve", "optimize", "refactor", "best practices"
        ]):
            review_skill = await self.skills.get_by_name("review")
            if review_skill:
                return review_skill

        # Fallback to LLM-based selection
        skills = await self.skills.list_skills()
        catalog = self.skills.get_skill_catalog(skills)
        if catalog:
            selection = await planner_llm.choose_skill(
                model=planner_model,
                user_input=user_input,
                skills=catalog,
            )
            selected_name = selection.get("skill_name")
            if isinstance(selected_name, str):
                explicit = await self.skills.get_by_name(selected_name)
                if explicit is not None:
                    return explicit

        return await self.skills.select_skill(user_input=user_input, skill_name=None)

    async def _extract_and_store_facts(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        text: str,
        memory_scope: str,
        context_key: str | None,
    ) -> None:
        """
        Extract and store important facts from user input
        Examples: names, preferences, context, dislikes, etc.
        """
        # Enhanced patterns to detect important information
        patterns = [
            # Name patterns - more comprehensive
            (r"(?:my name is|i'm|i am|call me|this is|i go by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", "name"),
            (r"(?:i'm called|they call me|people call me)\s+([A-Z][a-z]+)", "name"),
            
            # Preference patterns - more detailed
            (r"i (?:prefer|like|love|enjoy|want|need|use)\s+(.+?)(?:\.|$|,|\s+(?:and|but|because))", "preference"),
            (r"i (?:don't like|hate|dislike|avoid|never use)\s+(.+?)(?:\.|$|,|\s+(?:and|but|because))", "dislike"),
            (r"my favorite\s+(.+?)\s+is\s+(.+?)(?:\.|$|,)", "favorite"),
            
            # Context patterns - expanded
            (r"i(?:'m| am) (?:building|working on|developing|creating|making)\s+(.+?)(?:\.|$|,|\s+(?:using|with|for))", "project"),
            (r"i(?:'m| am) (?:a|an)\s+(.+?)(?:\.|$|,|\s+(?:at|in|for))", "role"),
            (r"i work (?:as|as a|as an)\s+(.+?)(?:\.|$|,)", "job_title"),
            
            # Location/company - enhanced
            (r"i work (?:at|for)\s+(.+?)(?:\.|$|,)", "company"),
            (r"i(?:'m| am) (?:from|in|based in|located in)\s+(.+?)(?:\.|$|,)", "location"),
            
            # Technology/tools
            (r"i (?:use|work with|code in|program in)\s+(.+?)(?:\.|$|,|\s+(?:and|for|to))", "technology"),
            (r"i(?:'m| am) learning\s+(.+?)(?:\.|$|,)", "learning"),
            
            # Goals/objectives
            (r"i want to\s+(.+?)(?:\.|$|,)", "goal"),
            (r"i(?:'m| am) trying to\s+(.+?)(?:\.|$|,)", "goal"),
            (r"my goal is to\s+(.+?)(?:\.|$|,)", "goal"),
            
            # Personal details
            (r"i have\s+(\d+)\s+years?\s+(?:of\s+)?experience", "experience_years"),
            (r"i(?:'m| am)\s+(\d+)\s+years?\s+old", "age"),
        ]
        
        import re
        facts_to_store = []
        
        for pattern, fact_type in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if fact_type == "favorite":
                    fact_value = f"{match.group(1)}: {match.group(2)}"
                else:
                    fact_value = match.group(1).strip()
                
                if fact_value and len(fact_value) > 1:
                    # Clean up the value
                    fact_value = fact_value.strip('.,!?')
                    facts_to_store.append({
                        "type": fact_type,
                        "value": fact_value,
                        "original": match.group(0)
                    })
        
        # Store each fact as structured memory
        for fact in facts_to_store:
            if fact['type'] == 'name':
                fact_text = f"User's name is {fact['value']}"
            elif fact['type'] == 'preference':
                fact_text = f"User prefers {fact['value']}"
            elif fact['type'] == 'dislike':
                fact_text = f"User dislikes {fact['value']}"
            elif fact['type'] == 'project':
                fact_text = f"User is working on {fact['value']}"
            elif fact['type'] == 'role':
                fact_text = f"User is a {fact['value']}"
            elif fact['type'] == 'company':
                fact_text = f"User works at {fact['value']}"
            elif fact['type'] == 'location':
                fact_text = f"User is from {fact['value']}"
            elif fact['type'] == 'technology':
                fact_text = f"User uses {fact['value']}"
            elif fact['type'] == 'goal':
                fact_text = f"User wants to {fact['value']}"
            else:
                fact_text = f"User {fact['type']}: {fact['value']}"
            
            # Store in vector store for retrieval
            await self.memory.vector_store_text(
                user_id=user_id,
                conversation_id=conversation_id,
                text=fact_text,
                memory_scope=memory_scope,
                context_key=context_key,
                metadata={
                    "type": "fact",
                    "fact_type": fact["type"],
                    "fact_value": fact["value"],
                    "role": "user_fact"
                },
            )
            
            # Store as structured memory
            await self.memory.store_structured(
                user_id=user_id,
                conversation_id=conversation_id,
                kind=f"fact_{fact['type']}",
                memory_scope=memory_scope,
                context_key=context_key,
                data={
                    "type": fact["type"],
                    "value": fact["value"],
                    "original_text": fact["original"],
                    "extracted_from": text[:100]
                },
            )
            
            logger.info(f"✓ Stored fact: {fact['type']} = {fact['value']}")
