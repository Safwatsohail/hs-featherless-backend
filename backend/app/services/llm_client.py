from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.app.core.config import get_settings


class LLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMResult:
    content: str
    raw: dict[str, Any]


class LLMClient:
    def __init__(
        self,
        *,
        provider: Literal["openai", "anthropic", "openrouter"] | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.settings = get_settings()
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def call_llm(
        self,
        *,
        provider: str,
        api_key: str,
        prompt: str,
        model: str | None = None,
    ) -> str:
        provider_name = provider or self.settings.default_llm_provider
        if provider_name in {"openai", "openrouter"}:
            return await self._call_openai(api_key=api_key, prompt=prompt, model=model)
        if provider_name == "anthropic":
            return await self._call_anthropic(api_key=api_key, prompt=prompt, model=model)
        raise ValueError(f"Unsupported provider: {provider_name}")

    async def generate(self, *, model: str, messages: list[dict[str, Any]], temperature: float = 0.2) -> LLMResult:
        provider_name = self.provider or self.settings.default_llm_provider
        api_key = self.api_key
        if not api_key:
            raise LLMError("LLM client requires an API key.")

        if provider_name in {"openai", "openrouter"}:
            data = await self._openai_chat(
                api_key=api_key,
                base_url=self.base_url or self._resolve_openai_compatible_base_url(provider_name),
                model=model,
                messages=messages,
                temperature=temperature,
                provider_name=provider_name,
            )
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return LLMResult(content=str(content or ""), raw=data)

        if provider_name == "anthropic":
            data = await self._anthropic_messages(
                api_key=api_key,
                base_url=self.base_url or self.settings.anthropic_base_url,
                model=model,
                messages=messages,
                temperature=temperature,
            )
            blocks = data.get("content") or []
            text = "".join([block.get("text", "") for block in blocks if isinstance(block, dict)])
            return LLMResult(content=text, raw=data)

        raise LLMError(f"Unsupported provider: {provider_name}")

    async def plan_tool_calls(
        self, *, model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        planner_system = (
            "You are a tool planner. Return JSON only.\n"
            "Schema: {\"tool_calls\": [{\"name\": \"tool_name\", \"input\": {}}]}\n"
            "Use only allowed tools. If no tool is needed, return {\"tool_calls\": []}."
        )
        planned = await self.generate(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": planner_system + "\nAllowed tools:\n" + json.dumps(tools)},
                *messages,
            ],
        )
        try:
            payload = json.loads(planned.content)
        except Exception:
            return {"tool_calls": []}
        if not isinstance(payload, dict) or not isinstance(payload.get("tool_calls"), list):
            return {"tool_calls": []}
        return payload

    async def choose_skill(
        self,
        *,
        model: str,
        user_input: str,
        skills: list[dict[str, Any]],
    ) -> dict[str, Any]:
        selector_prompt = (
            "Choose the best skill for the request.\n"
            "Return JSON only with schema: "
            "{\"skill_name\": \"name-or-null\", \"reason\": \"short reason\"}.\n"
            "Pick null only if none fit."
        )
        planned = await self.generate(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": selector_prompt},
                {
                    "role": "user",
                    "content": json.dumps({"request": user_input, "skills": skills}, ensure_ascii=False),
                },
            ],
        )
        try:
            payload = json.loads(planned.content)
        except Exception:
            return {"skill_name": None, "reason": "selector_parse_failed"}
        if not isinstance(payload, dict):
            return {"skill_name": None, "reason": "selector_invalid"}
        return {"skill_name": payload.get("skill_name"), "reason": payload.get("reason", "")}

    async def _call_openai(self, *, api_key: str, prompt: str, model: str | None) -> str:
        data = await self._openai_chat(
            api_key=api_key,
            base_url=self._resolve_openai_compatible_base_url(self.provider or self.settings.default_llm_provider),
            model=model or self.settings.default_llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            provider_name=self.provider or self.settings.default_llm_provider,
        )
        return data["choices"][0]["message"]["content"]

    async def _call_anthropic(self, *, api_key: str, prompt: str, model: str | None) -> str:
        data = await self._anthropic_messages(
            api_key=api_key,
            base_url=self.settings.anthropic_base_url,
            model=model or "claude-3-5-sonnet-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = data.get("content", [])
        if not content:
            return json.dumps(data)
        parts = [item.get("text", "") for item in content if item.get("type") == "text"]
        return "\n".join(part for part in parts if part).strip()

    async def _openai_chat(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        provider_name: str,
    ) -> dict[str, Any]:
        payload = {"model": model, "messages": messages, "temperature": temperature}
        headers = {"Authorization": f"Bearer {api_key}"}
        if provider_name == "openrouter":
            headers["HTTP-Referer"] = "https://localhost"
            headers["X-Title"] = "ai-orchestrator-backend"
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
            response = await client.post(
                "/chat/completions",
                headers=headers,
                json=payload,
            )
        if response.status_code >= 400:
            raise LLMError(f"{provider_name} error {response.status_code}: {response.text[:300]}")
        return response.json()

    def _resolve_openai_compatible_base_url(self, provider_name: str) -> str:
        if provider_name == "openrouter":
            return self.base_url or self.settings.openrouter_base_url
        return self.base_url or self.settings.openai_base_url

    async def _anthropic_messages(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
    ) -> dict[str, Any]:
        system = ""
        anthropic_messages = []
        for message in messages:
            role = message.get("role")
            if role == "system":
                system += str(message.get("content") or "") + "\n"
            elif role in {"user", "assistant"}:
                anthropic_messages.append({"role": role, "content": str(message.get("content") or "")})

        payload = {
            "model": model,
            "system": system.strip(),
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": 1024,
        }
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
            response = await client.post("/v1/messages", headers=headers, json=payload)
        if response.status_code >= 400:
            raise LLMError(f"Anthropic error {response.status_code}: {response.text[:300]}")
        return response.json()
