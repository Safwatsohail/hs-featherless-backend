from __future__ import annotations

import json
import logging
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
        if permitted_tools:
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
        if not tool_calls:
            tool_calls = self._fallback_tool_calls(
                skill_name=skill.name,
                user_input=user_input,
                skill_arguments=skill_arguments,
                permitted_tools=permitted_tools,
            )

        for tc in tool_calls:
            try:
                result = await self.tools.execute_tool(tc.name, tc.input)
                tool_outputs.append(
                    {"name": result.name, "output": result.output, "metadata": result.metadata}
                )
            except ToolError as exc:
                tool_outputs.append({"name": tc.name, "output": f"ToolError: {exc}", "metadata": {}})

        if tool_outputs:
            # Inject tool results as a user-role message so all providers accept it
            messages.append(
                {
                    "role": "user",
                    "content": "Tool results (use these to answer):\n" + json.dumps(tool_outputs, ensure_ascii=False),
                }
            )

        final = await llm.generate(model=selected_model, messages=messages)
        output_text = final.content.strip()
        
        # Clean up model's internal reasoning/thinking process
        # Some models include their reasoning in the response, we want just the final answer
        if "Here's my response to the given prompt:" in output_text:
            # Extract everything after this phrase
            parts = output_text.split("Here's my response to the given prompt:", 1)
            if len(parts) > 1:
                output_text = parts[1].strip().strip('"').strip()
        
        # Remove common thinking patterns
        thinking_patterns = [
            "I'm just a text-based model and don't have the ability to",
            "I can only respond based on the user prompt given to me.",
            "Here's my response to the given prompt:",
        ]
        for pattern in thinking_patterns:
            if pattern in output_text:
                # Try to extract just the actual answer
                lines = output_text.split('\n')
                cleaned_lines = []
                skip_mode = False
                for line in lines:
                    if any(p in line for p in thinking_patterns):
                        skip_mode = True
                        continue
                    if skip_mode and line.strip() and not any(p in line for p in thinking_patterns):
                        skip_mode = False
                    if not skip_mode:
                        cleaned_lines.append(line)
                if cleaned_lines:
                    output_text = '\n'.join(cleaned_lines).strip()
                break

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
            "\n=== RESPONSE EXCELLENCE GUIDELINES ===\n"
            "You are an elite AI assistant with access to powerful tools and comprehensive memory.\n"
            "Your responses should be 10x better than standard AI responses.\n\n"
            
            "CRITICAL: CODE FORMATTING RULES (MUST FOLLOW):\n"
            "- ALWAYS wrap code in proper markdown code blocks with language identifier\n"
            "- Format: ```python\\n[code here]\\n```\n"
            "- NEVER describe code in English paragraphs\n"
            "- NEVER say 'here is the code' or 'the function would look like'\n"
            "- ALWAYS provide actual, executable code with proper indentation\n"
            "- Use 4 spaces for Python indentation (not tabs)\n"
            "- Include proper syntax highlighting language tag (python, javascript, typescript, etc.)\n\n"
            
            "EXAMPLE - CORRECT:\n"
            "```python\n"
            "def fibonacci(n):\n"
            "    if n <= 1:\n"
            "        return n\n"
            "    return fibonacci(n-1) + fibonacci(n-2)\n"
            "```\n\n"
            
            "EXAMPLE - WRONG (DO NOT DO THIS):\n"
            "The function would calculate fibonacci by checking if n is less than or equal to 1...\n\n"
            
            "CORE PRINCIPLES:\n"
            "1. PERSONALIZATION: Use memory context to tailor responses to the user's specific situation\n"
            "2. DEPTH: Provide comprehensive, detailed answers with specific examples and data\n"
            "3. STRUCTURE: Use markdown formatting (headers, lists, code blocks, tables) for clarity\n"
            "4. ACTIONABILITY: Give concrete, implementable solutions with step-by-step guidance\n"
            "5. INTELLIGENCE: Synthesize information from multiple sources and tools\n\n"
            
            "RESPONSE FORMAT:\n"
            "- Start with a direct answer to the question\n"
            "- Use ## headers to organize sections\n"
            "- Include code examples in ```language blocks with proper syntax\n"
            "- Use bullet points for lists and key points\n"
            "- Add tables for comparisons when relevant\n"
            "- Include specific numbers, metrics, and data points\n"
            "- Cite sources when using tool results\n\n"
            
            "QUALITY STANDARDS:\n"
            "- Production-ready code (not pseudocode or descriptions)\n"
            "- Best practices and modern patterns\n"
            "- Security and performance considerations\n"
            "- Error handling and edge cases\n"
            "- Clear explanations of complex concepts\n"
            "- Real-world examples and use cases\n\n"
            
            "TOOL USAGE:\n"
            "- If tool results are provided, integrate them seamlessly into your response\n"
            "- Synthesize multiple tool outputs into a cohesive answer\n"
            "- Cite specific data points from tool results\n"
            "- Explain how the tool results answer the question\n\n"
            
            "WHAT TO AVOID:\n"
            "- Meta-commentary about being an AI or your limitations\n"
            "- Phrases like 'Here's my response' or 'I'm just a text-based model'\n"
            "- Vague or generic answers without specifics\n"
            "- Incomplete code examples or pseudocode\n"
            "- Describing code in English instead of showing actual code\n"
            "- Apologizing for not having information (just state what's needed)\n\n"
            
            "REMEMBER: You have access to tools, memory, and skills. Use them to provide\n"
            "responses that are comprehensive, personalized, and 10x more valuable than basic answers.\n"
            "When asked for code, ALWAYS provide actual code in proper markdown code blocks.\n"
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
        Intelligent fallback tool selection based on user intent.
        This ensures we ALWAYS use tools when they could be helpful.
        """
        normalized = f"{user_input}\n{skill_arguments or ''}".lower()
        tool_set = set(permitted_tools)
        calls: list[ToolCall] = []

        # PDF Analysis - highest priority for PDF files
        if "pdf_analyze" in tool_set:
            pdf_path = self._extract_local_path(normalized_source=user_input + "\n" + (skill_arguments or ""), suffix=".pdf")
            if pdf_path:
                calls.append(ToolCall(name="pdf_analyze", input={"path": pdf_path}))
                return calls

        # Deep Research - for comprehensive research queries
        if "deep_search" in tool_set and (
            skill_name == "deep_research"
            or any(term in normalized for term in [
                "deep research", "research", "latest", "compare", "investigate",
                "analyze", "study", "examine", "comprehensive", "detailed analysis",
                "what are the", "tell me about", "explain", "how does", "why is"
            ])
        ):
            calls.append(ToolCall(name="deep_search", input={"query": user_input}))
            return calls

        # Web Search - for any information lookup
        if "web_search" in tool_set and any(
            term in normalized for term in [
                "search", "look up", "find", "latest", "news", "current",
                "what is", "who is", "when did", "where is", "how to",
                "best", "top", "list", "compare", "vs", "versus",
                "2024", "2025", "recent", "new", "update"
            ]
        ):
            calls.append(ToolCall(name="web_search", input={"query": user_input}))
            # Don't return yet - might want to add more tools

        # Code Execution - for programming questions
        if "code_exec" in tool_set and any(
            term in normalized for term in [
                "run", "execute", "calculate", "compute", "evaluate",
                "python", "javascript", "code", "script", "function"
            ]
        ):
            # Try to extract code from the input
            if "```" in user_input:
                calls.append(ToolCall(name="code_exec", input={"code": user_input}))

        # Math Execution - for calculations
        if "math_exec" in tool_set and any(
            term in normalized for term in [
                "calculate", "compute", "sum", "average", "mean", "median",
                "total", "count", "percentage", "ratio", "+", "-", "*", "/",
                "equation", "formula", "solve"
            ]
        ):
            calls.append(ToolCall(name="math_exec", input={"expression": user_input}))

        # SQL Execution - for data queries
        if "sql_exec" in tool_set and any(
            term in normalized for term in [
                "query", "select", "database", "table", "data",
                "count", "sum", "average", "group by", "where",
                "analytics", "metrics", "stats", "statistics"
            ]
        ):
            # This would need actual SQL query extraction
            pass

        # File Operations
        if "file_read" in tool_set and any(
            term in normalized for term in ["read", "open", "show", "display", "content of"]
        ):
            # Try to extract file path
            import re
            file_match = re.search(r'["\']([^"\']+\.[a-z]{2,4})["\']', user_input)
            if file_match:
                calls.append(ToolCall(name="file_read", input={"path": file_match.group(1)}))

        # Image Analysis
        if "image_analyze" in tool_set and any(
            term in normalized for term in ["image", "picture", "photo", "screenshot", ".jpg", ".png", ".jpeg"]
        ):
            # Try to extract image path
            import re
            img_match = re.search(r'["\']([^"\']+\.(?:jpg|jpeg|png|gif|webp))["\']', user_input, re.IGNORECASE)
            if img_match:
                calls.append(ToolCall(name="image_analyze", input={"path": img_match.group(1)}))

        # API Calls - for external data
        if "api_call" in tool_set and any(
            term in normalized for term in ["api", "endpoint", "fetch", "get data", "retrieve"]
        ):
            # Try to extract URL
            import re
            url_match = re.search(r'https?://[^\s]+', user_input)
            if url_match:
                calls.append(ToolCall(name="api_call", input={"url": url_match.group(0)}))

        return calls

        if "code_analyze" in tool_set and (
            skill_name in {"codebase_analyst", "code_assistant", "debug", "review"}
            or any(term in normalized for term in ["codebase", "repo", "repository", "analyze code", "inspect code"])
        ):
            code_path = self._extract_local_path(
                normalized_source=user_input + "\n" + (skill_arguments or ""),
                suffix=None,
            ) or "."
            calls.append(ToolCall(name="code_analyze", input={"path": code_path, "query": user_input}))
            return calls

        return calls

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
