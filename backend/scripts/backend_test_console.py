from __future__ import annotations

import argparse
import getpass
import json
import sys
import uuid
from dataclasses import dataclass

import httpx


@dataclass
class SessionConfig:
    base_url: str
    provider: str
    model: str
    user_id: str
    memory_scope: str
    context_key: str


class BackendTestConsole:
    def __init__(self, *, client: httpx.Client, config: SessionConfig) -> None:
        self.client = client
        self.config = config

    def run(self) -> None:
        self._print_banner()
        self._health_check()
        self._show_catalog()
        while True:
            try:
                raw = input("\nbackend-test> ").strip()
            except EOFError:
                print()
                return

            if not raw:
                continue
            if raw in {"/quit", "/exit"}:
                return
            if raw == "/help":
                self._print_help()
                continue
            if raw == "/skills":
                self._print_json(self._request("GET", "/skills"))
                continue
            if raw == "/tools":
                self._print_json(self._request("GET", "/tools"))
                continue
            if raw.startswith("/memory "):
                text = raw.removeprefix("/memory ").strip()
                self._store_memory(text)
                continue
            if raw == "/context":
                self._show_context()
                continue
            if raw.startswith("/chat "):
                prompt = raw.removeprefix("/chat ").strip()
                self._chat(prompt=prompt)
                continue
            if raw.startswith("/skill "):
                payload = raw.removeprefix("/skill ").strip()
                skill_name, prompt, skill_arguments = self._parse_skill_command(payload)
                self._chat(prompt=prompt, skill_name=skill_name, skill_arguments=skill_arguments)
                continue
            print("Unknown command. Use /help.")

    def _print_banner(self) -> None:
        print("Backend Test Console")
        print(f"base_url={self.config.base_url}")
        print(f"provider={self.config.provider} model={self.config.model}")
        print(f"user_id={self.config.user_id}")
        print(f"memory_scope={self.config.memory_scope} context_key={self.config.context_key}")
        self._print_help()

    @staticmethod
    def _print_help() -> None:
        print("Commands:")
        print("  /help                    show commands")
        print("  /skills                  list skills")
        print("  /tools                   list tools")
        print("  /memory <text>           store manual memory")
        print("  /context                 fetch context snapshot")
        print("  /chat <prompt>           send prompt with auto skill selection")
        print("  /skill <name> :: <prompt> :: <arguments?>")
        print("                           call a specific skill")
        print("  /quit                    exit")

    def _health_check(self) -> None:
        result = self._request("GET", "/healthz")
        if result["status"] != 200:
            raise RuntimeError(f"Backend health check failed: {result}")
        print("healthz: ok")

    def _show_catalog(self) -> None:
        tools = self._request("GET", "/tools")
        skills = self._request("GET", "/skills")
        print(f"tools: {len(tools['body'])} available")
        print(f"skills: {len(skills['body'])} available")

    def _store_memory(self, text: str) -> None:
        result = self._request(
            "POST",
            "/memory",
            json={
                "user_id": self.config.user_id,
                "text": text,
                "kind": "manual_note",
                "memory_scope": self.config.memory_scope,
                "context_key": self.config.context_key,
                "metadata": {"source": "backend_test_console"},
            },
        )
        self._print_json(result)

    def _show_context(self) -> None:
        result = self._request(
            "GET",
            "/memory/context",
            params={
                "user_id": self.config.user_id,
                "query": "recent context",
                "memory_scope": self.config.memory_scope,
                "context_key": self.config.context_key,
            },
        )
        self._print_json(result)

    def _chat(
        self,
        *,
        prompt: str,
        skill_name: str | None = None,
        skill_arguments: str | None = None,
    ) -> None:
        result = self._request(
            "POST",
            "/chat",
            json={
                "user_id": self.config.user_id,
                "input": prompt,
                "provider": self.config.provider,
                "model": self.config.model,
                "skill_name": skill_name,
                "skill_arguments": skill_arguments,
                "memory_scope": self.config.memory_scope,
                "context_key": self.config.context_key,
            },
        )
        self._print_json(result)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        response = self.client.request(method, self.config.base_url + path, **kwargs)
        try:
            body = response.json()
        except Exception:
            body = response.text
        return {"status": response.status_code, "body": body}

    @staticmethod
    def _print_json(data: dict) -> None:
        print(json.dumps(data, indent=2, ensure_ascii=False))

    @staticmethod
    def _parse_skill_command(payload: str) -> tuple[str, str, str | None]:
        parts = [part.strip() for part in payload.split("::")]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise ValueError("Expected: /skill <name> :: <prompt> :: <arguments?>")
        skill_name = parts[0]
        prompt = parts[1]
        skill_arguments = parts[2] if len(parts) > 2 and parts[2] else None
        return skill_name, prompt, skill_arguments


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive backend API test console.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--provider", default="openrouter", choices=["openai", "anthropic", "openrouter"])
    parser.add_argument("--model", default="meta-llama/llama-3.3-8b-instruct:free")
    parser.add_argument("--user-id", default=str(uuid.uuid4()))
    parser.add_argument("--memory-scope", default="workspace", choices=["conversation", "user", "workspace", "global"])
    parser.add_argument("--context-key", default="backend-test")
    parser.add_argument("--api-key")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = args.api_key or getpass.getpass("Enter API key to save in backend: ").strip()
    if not api_key:
        print("API key is required.", file=sys.stderr)
        return 1

    config = SessionConfig(
        base_url=args.base_url.rstrip("/"),
        provider=args.provider,
        model=args.model,
        user_id=args.user_id,
        memory_scope=args.memory_scope,
        context_key=args.context_key,
    )
    with httpx.Client(timeout=60.0) as client:
        save_response = client.post(
            config.base_url + "/apikey",
            json={"user_id": config.user_id, "provider": config.provider, "api_key": api_key},
        )
        try:
            body = save_response.json()
        except Exception:
            body = save_response.text
        if save_response.status_code >= 400:
            print(json.dumps({"status": save_response.status_code, "body": body}, indent=2), file=sys.stderr)
            return 1

        print("API key saved.")
        console = BackendTestConsole(client=client, config=config)
        console.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

