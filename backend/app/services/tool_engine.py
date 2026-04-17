from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import httpx
from pypdf import PdfReader
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.tool import ToolDescriptor


class ToolError(RuntimeError):
    pass


@dataclass(frozen=True)
class ToolResult:
    name: str
    output: str
    metadata: dict[str, Any]


TOOL_DESCRIPTORS: list[ToolDescriptor] = [
    ToolDescriptor(
        name="python",
        description="Run small isolated Python snippets for deterministic calculations or transformations.",
        input_schema={"code": "string"},
    ),
    ToolDescriptor(
        name="bash",
        description="Run approved shell commands for workflow automation when allowed by skill tool rules.",
        input_schema={"command": "string"},
    ),
    ToolDescriptor(
        name="web_search",
        description="Search the web and return ranked search results with titles, URLs, and snippets.",
        input_schema={"query": "string", "max_results": "integer?"},
    ),
    ToolDescriptor(
        name="deep_search",
        description="Search the web, fetch top pages, and return consolidated source-backed excerpts.",
        input_schema={"query": "string", "max_results": "integer?", "max_pages": "integer?"},
    ),
    ToolDescriptor(
        name="url_fetch",
        description="Fetch a web page or text URL and extract a readable text preview.",
        input_schema={"url": "string", "max_chars": "integer?"},
    ),
    ToolDescriptor(
        name="pdf_analyze",
        description="Read a local PDF file and extract metadata, page count, and text preview.",
        input_schema={"path": "string", "max_pages": "integer?"},
    ),
    ToolDescriptor(
        name="code_analyze",
        description="Inspect a local file or directory and return structure, matches, and text excerpts.",
        input_schema={"path": "string", "query": "string?", "max_files": "integer?"},
    ),
    ToolDescriptor(
        name="db_query",
        description="Execute read-only SELECT or WITH SQL queries against PostgreSQL.",
        input_schema={"query": "string"},
    ),
]


class ToolEngine:
    def __init__(
        self,
        *,
        db: AsyncSession,
        python_timeout_seconds: int,
        bash_timeout_seconds: int,
        http_timeout_seconds: int,
        web_search_max_results: int,
        deep_search_max_pages: int,
    ) -> None:
        self.db = db
        self.python_timeout_seconds = python_timeout_seconds
        self.bash_timeout_seconds = bash_timeout_seconds
        self.http_timeout_seconds = http_timeout_seconds
        self.web_search_max_results = web_search_max_results
        self.deep_search_max_pages = deep_search_max_pages

    def list_tools(self) -> list[ToolDescriptor]:
        return TOOL_DESCRIPTORS

    def get_tool_specs(self, names: list[str]) -> list[dict[str, Any]]:
        allowed = set(names)
        return [tool.model_dump() for tool in TOOL_DESCRIPTORS if tool.name in allowed]

    async def execute_tool(self, tool_name: str, tool_input: dict) -> ToolResult:
        if tool_name == "python":
            return self._python(tool_input)
        if tool_name == "bash":
            return self._bash(tool_input)
        if tool_name == "web_search":
            return await self._web_search(tool_input)
        if tool_name == "deep_search":
            return await self._deep_search(tool_input)
        if tool_name == "url_fetch":
            return await self._url_fetch(tool_input)
        if tool_name == "pdf_analyze":
            return self._pdf_analyze(tool_input)
        if tool_name == "code_analyze":
            return self._code_analyze(tool_input)
        if tool_name == "db_query":
            return await self._db_query(tool_input)
        raise ToolError(f"Unknown tool: {tool_name}")

    def _python(self, tool_input: dict) -> ToolResult:
        code = str(tool_input.get("code") or "")
        if not code.strip():
            raise ToolError("python tool requires non-empty 'code'.")

        with tempfile.TemporaryDirectory(prefix="tool_py_") as td:
            proc = subprocess.run(
                [sys.executable, "-I", "-c", code],
                cwd=td,
                capture_output=True,
                text=True,
                timeout=self.python_timeout_seconds,
                env={},
            )
        out = (proc.stdout or "") + (proc.stderr or "")
        return ToolResult(name="python", output=out.strip(), metadata={"returncode": proc.returncode})

    def _bash(self, tool_input: dict) -> ToolResult:
        command = str(tool_input.get("command") or "").strip()
        if not command:
            raise ToolError("bash tool requires non-empty 'command'.")

        proc = subprocess.run(
            ["bash", "-lc", command],
            capture_output=True,
            text=True,
            timeout=self.bash_timeout_seconds,
            env={},
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return ToolResult(
            name="bash",
            output=out.strip(),
            metadata={"returncode": proc.returncode, "command": command},
        )

    async def _web_search(self, tool_input: dict) -> ToolResult:
        query = str(tool_input.get("query") or "").strip()
        if not query:
            raise ToolError("web_search tool requires 'query'.")

        max_results = min(int(tool_input.get("max_results") or self.web_search_max_results), 10)
        async with httpx.AsyncClient(timeout=self.http_timeout_seconds, follow_redirects=True) as client:
            response = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers={"user-agent": "Mozilla/5.0"},
            )
        if response.status_code >= 400:
            raise ToolError(f"web_search failed with status {response.status_code}")

        results = self._parse_duckduckgo_results(response.text, max_results=max_results)
        return ToolResult(
            name="web_search",
            output=json.dumps({"query": query, "results": results}, ensure_ascii=False),
            metadata={"count": len(results)},
        )

    async def _deep_search(self, tool_input: dict) -> ToolResult:
        query = str(tool_input.get("query") or "").strip()
        if not query:
            raise ToolError("deep_search tool requires 'query'.")

        max_results = min(int(tool_input.get("max_results") or self.web_search_max_results), 10)
        max_pages = min(int(tool_input.get("max_pages") or self.deep_search_max_pages), 5)

        search_result = await self._web_search({"query": query, "max_results": max_results})
        payload = json.loads(search_result.output)
        pages = []
        for item in payload.get("results", [])[:max_pages]:
            url = item.get("url")
            if not url:
                continue
            try:
                fetched = await self._url_fetch({"url": url, "max_chars": 2500})
            except Exception as exc:  # noqa: BLE001
                pages.append({"url": url, "error": str(exc)})
                continue
            pages.append(
                {
                    "title": item.get("title"),
                    "url": url,
                    "snippet": item.get("snippet"),
                    "content": fetched.output,
                }
            )

        return ToolResult(
            name="deep_search",
            output=json.dumps({"query": query, "results": payload.get("results", []), "pages": pages}, ensure_ascii=False),
            metadata={"search_results": len(payload.get("results", [])), "pages_fetched": len(pages)},
        )

    async def _url_fetch(self, tool_input: dict) -> ToolResult:
        url = str(tool_input.get("url") or "").strip()
        if not url:
            raise ToolError("url_fetch tool requires 'url'.")

        max_chars = min(int(tool_input.get("max_chars") or 4000), 20000)
        async with httpx.AsyncClient(timeout=self.http_timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url, headers={"user-agent": "Mozilla/5.0"})
        if response.status_code >= 400:
            raise ToolError(f"url_fetch failed with status {response.status_code}")

        content_type = response.headers.get("content-type", "")
        text = response.text
        if "html" in content_type:
            text = self._html_to_text(text)
        text = text.strip()[:max_chars]
        return ToolResult(
            name="url_fetch",
            output=text,
            metadata={"url": url, "content_type": content_type, "chars": len(text)},
        )

    def _pdf_analyze(self, tool_input: dict) -> ToolResult:
        path = Path(str(tool_input.get("path") or "")).expanduser()
        if not path.exists():
            raise ToolError(f"pdf_analyze path does not exist: {path}")
        if path.suffix.lower() != ".pdf":
            raise ToolError("pdf_analyze only supports local .pdf files.")

        max_pages = min(int(tool_input.get("max_pages") or 5), 20)
        reader = PdfReader(str(path))
        preview_parts = []
        for index, page in enumerate(reader.pages[:max_pages]):
            text = (page.extract_text() or "").strip()
            if text:
                preview_parts.append(f"[Page {index + 1}]\n{text[:2000]}")

        payload = {
            "path": str(path),
            "pages": len(reader.pages),
            "metadata": {str(k): str(v) for k, v in (reader.metadata or {}).items()},
            "preview": "\n\n".join(preview_parts),
        }
        return ToolResult(name="pdf_analyze", output=json.dumps(payload, ensure_ascii=False), metadata={"pages": len(reader.pages)})

    def _code_analyze(self, tool_input: dict) -> ToolResult:
        path = Path(str(tool_input.get("path") or "")).expanduser()
        if not path.exists():
            raise ToolError(f"code_analyze path does not exist: {path}")

        query = str(tool_input.get("query") or "").strip()
        max_files = min(int(tool_input.get("max_files") or 10), 50)

        if path.is_file():
            content = path.read_text(encoding="utf-8", errors="ignore")
            return ToolResult(
                name="code_analyze",
                output=json.dumps(
                    {
                        "path": str(path),
                        "type": "file",
                        "size": path.stat().st_size,
                        "preview": content[:5000],
                        "matches_query": bool(query and query.lower() in content.lower()),
                    },
                    ensure_ascii=False,
                ),
                metadata={"files": 1},
            )

        files = [p for p in path.rglob("*") if p.is_file()]
        files = sorted(files)[:max_files]
        summary = []
        for file in files:
            item = {
                "path": str(file),
                "size": file.stat().st_size,
            }
            if query:
                content = file.read_text(encoding="utf-8", errors="ignore")
                idx = content.lower().find(query.lower())
                if idx >= 0:
                    item["match_excerpt"] = content[max(idx - 200, 0) : idx + 600]
            summary.append(item)

        return ToolResult(
            name="code_analyze",
            output=json.dumps(
                {"path": str(path), "type": "directory", "file_count": len(files), "files": summary},
                ensure_ascii=False,
            ),
            metadata={"files": len(files)},
        )

    async def _db_query(self, tool_input: dict) -> ToolResult:
        query = str(tool_input.get("query") or "").strip()
        if not query:
            raise ToolError("db_query tool requires 'query'.")
        if not re.match(r"^(with\\s+|select\\s+)", query, flags=re.IGNORECASE):
            raise ToolError("db_query only allows SELECT/WITH queries.")

        res = await self.db.execute(sql_text(query))
        rows = res.mappings().fetchmany(50)
        return ToolResult(name="db_query", output=json.dumps([dict(r) for r in rows], default=str), metadata={})

    @staticmethod
    def _parse_duckduckgo_results(html: str, *, max_results: int) -> list[dict[str, str]]:
        matches = re.findall(
            r'nofollow" class="result__a" href="(?P<href>[^"]+)">(?P<title>.*?)</a>.*?<a class="result__snippet".*?>(?P<snippet>.*?)</a>',
            html,
            flags=re.DOTALL,
        )
        results = []
        for href, title, snippet in matches[:max_results]:
            clean_url = unquote(href)
            if "uddg=" in clean_url:
                clean_url = clean_url.split("uddg=", 1)[1]
            results.append(
                {
                    "title": ToolEngine._strip_html(title),
                    "url": clean_url,
                    "snippet": ToolEngine._strip_html(snippet),
                }
            )
        return results

    @staticmethod
    def _html_to_text(html: str) -> str:
        text = re.sub(r"<script.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _strip_html(value: str) -> str:
        return ToolEngine._html_to_text(value).strip()
