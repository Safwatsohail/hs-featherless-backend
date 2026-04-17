from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.conversation import Conversation, Message
from backend.app.schemas.chat import ToolCall
from backend.app.services.api_key_service import ApiKeyService
from backend.app.services.llm_client import LLMClient, LLMError
from backend.app.services.memory_engine import MemoryEngine
from backend.app.services.skill_engine import SkillEngine
from backend.app.services.tool_engine import ToolEngine, ToolError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrchestratorResult:
    conversation_id: uuid.UUID
    skill: str
    tool_calls: list[ToolCall]
    output: str


class Orchestrator:
    assistant_memory_max_chars = 500

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
        selected_model = model or self.default_model
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
            planner_tools = self.tools.get_tool_specs(permitted_tools)
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
            messages.append(
                {
                    "role": "system",
                    "content": "Tool results:\n" + json.dumps(tool_outputs, ensure_ascii=False),
                }
            )

        final = await llm.generate(model=selected_model, messages=messages)
        output_text = final.content.strip()

        await self._store_turn(
            user_id=user_id,
            conversation_id=conv.id,
            user_input=user_input,
            assistant_output=output_text,
            tool_calls=tool_calls,
            tool_outputs=tool_outputs,
            memory_scope=memory_scope,
            context_key=context_key,
        )

        return OrchestratorResult(
            conversation_id=conv.id,
            skill=skill.name,
            tool_calls=tool_calls,
            output=output_text,
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
        if conversation_id:
            res = await self.db.execute(select(Conversation).where(Conversation.id == conversation_id))
            conv = res.scalar_one_or_none()
            if conv and conv.user_id == user_id:
                return conv

        conv = Conversation(user_id=user_id, title=title, memory_scope=memory_scope, context_key=context_key)
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
        if short_msgs:
            parts.append("Short-term conversation context:\n")
            for m in short_msgs:
                parts.append(f"- {m.role}: {m.content}\n")
            parts.append("\n")
        if vector_hits:
            parts.append("Relevant long-term memory:\n")
            for h in vector_hits:
                text = str(h.get("text") or "")[:800]
                parts.append(f"- {text}\n")
        return "".join(parts).strip()

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

    async def _store_turn(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_input: str,
        assistant_output: str,
        tool_calls: list[ToolCall],
        tool_outputs: list[dict],
        memory_scope: str,
        context_key: str | None,
    ) -> None:
        self.db.add(
            Message(conversation_id=conversation_id, user_id=user_id, role="user", content=user_input)
        )
        self.db.add(
            Message(
                conversation_id=conversation_id, user_id=user_id, role="assistant", content=assistant_output
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
            data={"user_input": user_input, "assistant_output": assistant_output},
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
