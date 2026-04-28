from __future__ import annotations

import base64
import csv
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import unquote
import uuid

import httpx
from pypdf import PdfReader
from sqlalchemy import select, text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.external_tool import ExternalTool
from app.schemas.tool import ExternalToolCreate
from app.schemas.tool import ToolDescriptor


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

EXTRA_TOOL_DESCRIPTORS: list[ToolDescriptor] = [
    ToolDescriptor(name="docs_search", description="Search documentation-focused web results.", input_schema={"query": "string"}),
    ToolDescriptor(name="news_search", description="Search recent web/news-style results.", input_schema={"query": "string"}),
    ToolDescriptor(name="academic_search", description="Search research-leaning sources and pages.", input_schema={"query": "string"}),
    ToolDescriptor(name="company_search", description="Search for company pages, product pages, and official websites.", input_schema={"query": "string"}),
    ToolDescriptor(name="people_search", description="Search for public information about people and profiles.", input_schema={"query": "string"}),
    ToolDescriptor(name="market_search", description="Search for market, competitor, and pricing information.", input_schema={"query": "string"}),
    ToolDescriptor(name="issue_search", description="Search for issue reports, troubleshooting pages, and error discussions.", input_schema={"query": "string"}),
    ToolDescriptor(name="source_research", description="Run deep multi-source research over fetched pages.", input_schema={"query": "string"}),
    ToolDescriptor(name="compare_sources", description="Search and compare multiple source pages for a topic.", input_schema={"query": "string"}),
    ToolDescriptor(name="fact_check_search", description="Search multiple sources to verify a factual claim.", input_schema={"query": "string"}),
    ToolDescriptor(name="webpage_preview", description="Fetch a page and return a short readable preview.", input_schema={"url": "string"}),
    ToolDescriptor(name="page_text", description="Fetch a page and return extracted plain text.", input_schema={"url": "string"}),
    ToolDescriptor(name="page_metadata", description="Fetch a page and return title, content type, and metadata preview.", input_schema={"url": "string"}),
    ToolDescriptor(name="link_extract", description="Fetch a page and extract links from it.", input_schema={"url": "string"}),
    ToolDescriptor(name="html_extract", description="Convert HTML input into readable text.", input_schema={"html": "string"}),
    ToolDescriptor(name="file_read", description="Read a local file and preview its contents.", input_schema={"path": "string"}),
    ToolDescriptor(name="directory_map", description="List a local directory structure and file summaries.", input_schema={"path": "string"}),
    ToolDescriptor(name="repo_overview", description="Summarize a local repository structure.", input_schema={"path": "string?"}),
    ToolDescriptor(name="grep_files", description="Search local files for a query and return matches.", input_schema={"path": "string?", "query": "string"}),
    ToolDescriptor(name="text_stats", description="Compute basic statistics for a text block.", input_schema={"text": "string"}),
    ToolDescriptor(name="regex_extract", description="Apply a regex pattern and return matches.", input_schema={"text": "string", "pattern": "string"}),
    ToolDescriptor(name="extract_urls", description="Extract URLs from free-form text.", input_schema={"text": "string"}),
    ToolDescriptor(name="extract_emails", description="Extract email addresses from free-form text.", input_schema={"text": "string"}),
    ToolDescriptor(name="slugify_text", description="Convert free-form text into a slug.", input_schema={"text": "string"}),
    ToolDescriptor(name="line_count", description="Count lines, words, and characters in text.", input_schema={"text": "string"}),
    ToolDescriptor(name="hash_text", description="Hash text with a deterministic digest.", input_schema={"text": "string", "algorithm": "string?"}),
    ToolDescriptor(name="base64_encode", description="Encode text as base64.", input_schema={"text": "string"}),
    ToolDescriptor(name="base64_decode", description="Decode base64 text.", input_schema={"text": "string"}),
    ToolDescriptor(name="uuid_generate", description="Generate one or more UUIDs.", input_schema={"count": "integer?"}),
    ToolDescriptor(name="timestamp_now", description="Return the current UTC timestamp.", input_schema={}),
    ToolDescriptor(name="json_pretty", description="Pretty-print JSON text or objects.", input_schema={"value": "any"}),
    ToolDescriptor(name="csv_preview", description="Preview CSV content from text or a local file path.", input_schema={"text": "string?", "path": "string?"}),
    ToolDescriptor(name="csv_to_json", description="Convert CSV content from text or file into JSON rows.", input_schema={"text": "string?", "path": "string?"}),
    ToolDescriptor(name="markdown_preview", description="Preview markdown content from text or file.", input_schema={"text": "string?", "path": "string?"}),
    ToolDescriptor(name="html_to_text", description="Convert HTML into plain text.", input_schema={"html": "string"}),
    ToolDescriptor(name="calculator", description="Evaluate a simple arithmetic expression.", input_schema={"expression": "string"}),
    ToolDescriptor(name="table_preview", description="Preview rows from CSV or JSON-like tabular text.", input_schema={"text": "string"}),
    ToolDescriptor(name="query_inspector", description="Inspect a SQL query and classify its type.", input_schema={"query": "string"}),
    ToolDescriptor(name="json_keys", description="List top-level keys from a JSON object.", input_schema={"value": "any"}),
    ToolDescriptor(name="text_trim", description="Trim text to a maximum number of characters.", input_schema={"text": "string", "max_chars": "integer?"}),
    ToolDescriptor(name="keyword_extract", description="Extract repeated keywords from text.", input_schema={"text": "string"}),
    ToolDescriptor(name="reading_time", description="Estimate reading time for a text block.", input_schema={"text": "string"}),
    ToolDescriptor(name="sentence_split", description="Split text into individual sentences.", input_schema={"text": "string"}),
    ToolDescriptor(name="list_files", description="List files inside a local path.", input_schema={"path": "string?"}),
    ToolDescriptor(name="path_exists", description="Check whether a local path exists.", input_schema={"path": "string"}),
    ToolDescriptor(name="mime_guess", description="Guess the file type from a local path.", input_schema={"path": "string"}),
    ToolDescriptor(name="search_memory_hints", description="Generate memory-oriented search hints from a request.", input_schema={"query": "string"}),
]

ALL_TOOL_DESCRIPTORS: list[ToolDescriptor] = [*TOOL_DESCRIPTORS, *EXTRA_TOOL_DESCRIPTORS]

WEB_SEARCH_ALIASES = {
    "docs_search": "documentation ",
    "news_search": "latest news ",
    "academic_search": "research paper ",
    "company_search": "official company site ",
    "people_search": "person profile ",
    "market_search": "market competitor pricing ",
    "issue_search": "issue troubleshooting ",
}

DEEP_SEARCH_ALIASES = {
    "source_research": "",
    "compare_sources": "compare ",
    "fact_check_search": "fact check ",
}


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

    async def list_tools(self) -> list[ToolDescriptor]:
        external = await self.list_external_tools()
        return [*ALL_TOOL_DESCRIPTORS, *external]

    async def get_tool_specs(self, names: list[str]) -> list[dict[str, Any]]:
        allowed = set(names)
        builtins = [tool.model_dump() for tool in ALL_TOOL_DESCRIPTORS if tool.name in allowed]
        external = [tool.model_dump() for tool in await self.list_external_tools() if tool.name in allowed]
        return [*builtins, *external]

    async def execute_tool(self, tool_name: str, tool_input: dict) -> ToolResult:
        if tool_name in WEB_SEARCH_ALIASES:
            return await self._web_search_alias(tool_name, tool_input)
        if tool_name in DEEP_SEARCH_ALIASES:
            return await self._deep_search_alias(tool_name, tool_input)
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
        if tool_name == "webpage_preview":
            return await self._url_fetch(tool_input)
        if tool_name == "page_text":
            return await self._url_fetch(tool_input)
        if tool_name == "page_metadata":
            return await self._page_metadata(tool_input)
        if tool_name == "link_extract":
            return await self._link_extract(tool_input)
        if tool_name in {"html_extract", "html_to_text"}:
            return self._html_extract(tool_input)
        if tool_name == "file_read":
            return self._file_read(tool_input)
        if tool_name == "directory_map":
            return self._directory_map(tool_input)
        if tool_name == "repo_overview":
            return self._repo_overview(tool_input)
        if tool_name == "grep_files":
            return self._grep_files(tool_input)
        if tool_name == "text_stats":
            return self._text_stats(tool_input)
        if tool_name == "regex_extract":
            return self._regex_extract(tool_input)
        if tool_name == "extract_urls":
            return self._extract_urls(tool_input)
        if tool_name == "extract_emails":
            return self._extract_emails(tool_input)
        if tool_name == "slugify_text":
            return self._slugify_text(tool_input)
        if tool_name == "line_count":
            return self._line_count(tool_input)
        if tool_name == "hash_text":
            return self._hash_text(tool_input)
        if tool_name == "base64_encode":
            return self._base64_encode(tool_input)
        if tool_name == "base64_decode":
            return self._base64_decode(tool_input)
        if tool_name == "uuid_generate":
            return self._uuid_generate(tool_input)
        if tool_name == "timestamp_now":
            return self._timestamp_now()
        if tool_name == "json_pretty":
            return self._json_pretty(tool_input)
        if tool_name == "csv_preview":
            return self._csv_preview(tool_input)
        if tool_name == "csv_to_json":
            return self._csv_to_json(tool_input)
        if tool_name == "markdown_preview":
            return self._markdown_preview(tool_input)
        if tool_name == "calculator":
            return self._calculator(tool_input)
        if tool_name == "table_preview":
            return self._table_preview(tool_input)
        if tool_name == "query_inspector":
            return self._query_inspector(tool_input)
        if tool_name == "json_keys":
            return self._json_keys(tool_input)
        if tool_name == "text_trim":
            return self._text_trim(tool_input)
        if tool_name == "keyword_extract":
            return self._keyword_extract(tool_input)
        if tool_name == "reading_time":
            return self._reading_time(tool_input)
        if tool_name == "sentence_split":
            return self._sentence_split(tool_input)
        if tool_name == "list_files":
            return self._list_files(tool_input)
        if tool_name == "path_exists":
            return self._path_exists(tool_input)
        if tool_name == "mime_guess":
            return self._mime_guess(tool_input)
        if tool_name == "search_memory_hints":
            return self._search_memory_hints(tool_input)
        external_tool = await self.get_external_tool(tool_name)
        if external_tool is not None:
            return await self._external_tool(external_tool, tool_input)
        raise ToolError(f"Unknown tool: {tool_name}")

    async def create_external_tool(self, payload: ExternalToolCreate) -> ExternalTool:
        existing = await self.get_external_tool(payload.name)
        if existing is not None:
            raise ToolError(f"External tool '{payload.name}' already exists.")
        row = ExternalTool(
            name=payload.name,
            description=payload.description,
            endpoint_url=payload.endpoint_url,
            method=payload.method,
            headers=payload.headers,
            input_schema=payload.input_schema,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def list_external_tools(self) -> list[ToolDescriptor]:
        result = await self.db.execute(
            select(ExternalTool).where(ExternalTool.active.is_(True)).order_by(ExternalTool.name.asc())
        )
        rows = list(result.scalars().all())
        return [
            ToolDescriptor(name=row.name, description=row.description, input_schema=row.input_schema or {})
            for row in rows
        ]

    async def get_external_tool(self, name: str) -> ExternalTool | None:
        result = await self.db.execute(
            select(ExternalTool).where(ExternalTool.name == name, ExternalTool.active.is_(True))
        )
        return result.scalar_one_or_none()

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

    async def _external_tool(self, tool: ExternalTool, tool_input: dict) -> ToolResult:
        async with httpx.AsyncClient(timeout=self.http_timeout_seconds, follow_redirects=True) as client:
            response = await client.request(
                tool.method.upper(),
                tool.endpoint_url,
                headers={str(k): str(v) for k, v in (tool.headers or {}).items()},
                json=tool_input,
            )
        if response.status_code >= 400:
            raise ToolError(f"external tool '{tool.name}' failed with status {response.status_code}")
        content_type = response.headers.get("content-type", "")
        try:
            payload = response.json()
            output = json.dumps(payload, ensure_ascii=False)
        except Exception:
            output = response.text[:20000]
        return ToolResult(
            name=tool.name,
            output=output,
            metadata={"status_code": response.status_code, "content_type": content_type},
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
        if not re.match(r"^(with\s+|select\s+)", query, flags=re.IGNORECASE):
            raise ToolError("db_query only allows SELECT/WITH queries.")

        res = await self.db.execute(sql_text(query))
        rows = res.mappings().fetchmany(50)
        return ToolResult(name="db_query", output=json.dumps([dict(r) for r in rows], default=str), metadata={})

    async def _web_search_alias(self, tool_name: str, tool_input: dict) -> ToolResult:
        query = str(tool_input.get("query") or "").strip()
        prefix = WEB_SEARCH_ALIASES.get(tool_name, "")
        return await self._web_search({"query": f"{prefix}{query}".strip(), "max_results": tool_input.get("max_results")})

    async def _deep_search_alias(self, tool_name: str, tool_input: dict) -> ToolResult:
        query = str(tool_input.get("query") or "").strip()
        prefix = DEEP_SEARCH_ALIASES.get(tool_name, "")
        return await self._deep_search(
            {
                "query": f"{prefix}{query}".strip(),
                "max_results": tool_input.get("max_results"),
                "max_pages": tool_input.get("max_pages"),
            }
        )

    async def _page_metadata(self, tool_input: dict) -> ToolResult:
        url = str(tool_input.get("url") or "").strip()
        if not url:
            raise ToolError("page_metadata tool requires 'url'.")
        async with httpx.AsyncClient(timeout=self.http_timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url, headers={"user-agent": "Mozilla/5.0"})
        if response.status_code >= 400:
            raise ToolError(f"page_metadata failed with status {response.status_code}")
        title_match = re.search(r"<title>(.*?)</title>", response.text, flags=re.IGNORECASE | re.DOTALL)
        links = re.findall(r'href=["\\\']([^"\\\']+)["\\\']', response.text, flags=re.IGNORECASE)
        payload = {
            "url": url,
            "content_type": response.headers.get("content-type", ""),
            "title": self._strip_html(title_match.group(1)) if title_match else "",
            "link_count": len(links),
        }
        return ToolResult(name="page_metadata", output=json.dumps(payload, ensure_ascii=False), metadata=payload)

    async def _link_extract(self, tool_input: dict) -> ToolResult:
        url = str(tool_input.get("url") or "").strip()
        if not url:
            raise ToolError("link_extract tool requires 'url'.")
        async with httpx.AsyncClient(timeout=self.http_timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url, headers={"user-agent": "Mozilla/5.0"})
        if response.status_code >= 400:
            raise ToolError(f"link_extract failed with status {response.status_code}")
        links = re.findall(r'href=["\\\']([^"\\\']+)["\\\']', response.text, flags=re.IGNORECASE)
        payload = {"url": url, "links": links[:50]}
        return ToolResult(name="link_extract", output=json.dumps(payload, ensure_ascii=False), metadata={"count": len(links)})

    def _html_extract(self, tool_input: dict) -> ToolResult:
        html = str(tool_input.get("html") or "")
        text = self._html_to_text(html)
        return ToolResult(name="html_extract", output=text, metadata={"chars": len(text)})

    def _file_read(self, tool_input: dict) -> ToolResult:
        path = Path(str(tool_input.get("path") or "")).expanduser()
        if not path.exists() or not path.is_file():
            raise ToolError(f"file_read path does not exist: {path}")
        content = path.read_text(encoding="utf-8", errors="ignore")
        payload = {"path": str(path), "size": path.stat().st_size, "preview": content[:8000]}
        return ToolResult(name="file_read", output=json.dumps(payload, ensure_ascii=False), metadata={"size": path.stat().st_size})

    def _directory_map(self, tool_input: dict) -> ToolResult:
        path = Path(str(tool_input.get("path") or ".")).expanduser()
        if not path.exists() or not path.is_dir():
            raise ToolError(f"directory_map path does not exist: {path}")
        files = sorted([p for p in path.rglob("*") if p.is_file()])[:100]
        payload = {"path": str(path), "files": [str(file) for file in files], "count": len(files)}
        return ToolResult(name="directory_map", output=json.dumps(payload, ensure_ascii=False), metadata={"count": len(files)})

    def _repo_overview(self, tool_input: dict) -> ToolResult:
        return self._directory_map({"path": tool_input.get("path") or "."})

    def _grep_files(self, tool_input: dict) -> ToolResult:
        return self._code_analyze(
            {
                "path": tool_input.get("path") or ".",
                "query": tool_input.get("query") or "",
                "max_files": tool_input.get("max_files") or 20,
            }
        )

    def _text_stats(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        lines = text.splitlines() or [text]
        words = re.findall(r"\S+", text)
        payload = {"chars": len(text), "words": len(words), "lines": len(lines)}
        return ToolResult(name="text_stats", output=json.dumps(payload), metadata=payload)

    def _regex_extract(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        pattern = str(tool_input.get("pattern") or "")
        if not pattern:
            raise ToolError("regex_extract requires 'pattern'.")
        matches = re.findall(pattern, text)
        return ToolResult(name="regex_extract", output=json.dumps({"matches": matches}, ensure_ascii=False), metadata={"count": len(matches)})

    def _extract_urls(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        matches = re.findall(r"https?://\S+", text)
        return ToolResult(name="extract_urls", output=json.dumps({"urls": matches}, ensure_ascii=False), metadata={"count": len(matches)})

    def _extract_emails(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        matches = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        return ToolResult(name="extract_emails", output=json.dumps({"emails": matches}, ensure_ascii=False), metadata={"count": len(matches)})

    def _slugify_text(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        return ToolResult(name="slugify_text", output=slug, metadata={"chars": len(slug)})

    def _line_count(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        payload = {"lines": len(text.splitlines()), "words": len(re.findall(r"\S+", text)), "chars": len(text)}
        return ToolResult(name="line_count", output=json.dumps(payload), metadata=payload)

    def _hash_text(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        algorithm = str(tool_input.get("algorithm") or "sha256").lower()
        if algorithm not in {"sha1", "sha256", "md5"}:
            raise ToolError("hash_text only supports md5, sha1, sha256.")
        digest = getattr(hashlib, algorithm)(text.encode("utf-8")).hexdigest()
        return ToolResult(name="hash_text", output=digest, metadata={"algorithm": algorithm})

    def _base64_encode(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        return ToolResult(name="base64_encode", output=base64.b64encode(text.encode("utf-8")).decode("utf-8"), metadata={})

    def _base64_decode(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        try:
            decoded = base64.b64decode(text.encode("utf-8")).decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"base64_decode failed: {exc}") from exc
        return ToolResult(name="base64_decode", output=decoded, metadata={})

    def _uuid_generate(self, tool_input: dict) -> ToolResult:
        count = min(int(tool_input.get("count") or 1), 20)
        values = [str(uuid.uuid4()) for _ in range(count)]
        return ToolResult(name="uuid_generate", output=json.dumps({"uuids": values}), metadata={"count": count})

    def _timestamp_now(self) -> ToolResult:
        now = datetime.now(timezone.utc).isoformat()
        return ToolResult(name="timestamp_now", output=now, metadata={"timezone": "UTC"})

    def _json_pretty(self, tool_input: dict) -> ToolResult:
        value = tool_input.get("value")
        if isinstance(value, str):
            value = json.loads(value)
        return ToolResult(name="json_pretty", output=json.dumps(value, indent=2, ensure_ascii=False), metadata={})

    @staticmethod
    def _csv_source(tool_input: dict) -> str:
        text = tool_input.get("text")
        path = tool_input.get("path")
        if text:
            return str(text)
        if path:
            return Path(str(path)).expanduser().read_text(encoding="utf-8", errors="ignore")
        raise ToolError("CSV tool requires either 'text' or 'path'.")

    def _csv_preview(self, tool_input: dict) -> ToolResult:
        source = self._csv_source(tool_input)
        reader = csv.DictReader(StringIO(source))
        rows = []
        for _, row in zip(range(5), reader, strict=False):
            rows.append(row)
        return ToolResult(name="csv_preview", output=json.dumps({"rows": rows}, ensure_ascii=False), metadata={"rows": len(rows)})

    def _csv_to_json(self, tool_input: dict) -> ToolResult:
        source = self._csv_source(tool_input)
        reader = csv.DictReader(StringIO(source))
        rows = list(reader)
        return ToolResult(name="csv_to_json", output=json.dumps(rows, ensure_ascii=False), metadata={"rows": len(rows)})

    def _markdown_preview(self, tool_input: dict) -> ToolResult:
        text = tool_input.get("text")
        path = tool_input.get("path")
        if path:
            text = Path(str(path)).expanduser().read_text(encoding="utf-8", errors="ignore")
        if text is None:
            raise ToolError("markdown_preview requires 'text' or 'path'.")
        plain = re.sub(r"[#*_>`-]+", " ", str(text))
        plain = re.sub(r"\s+", " ", plain).strip()
        return ToolResult(name="markdown_preview", output=plain[:4000], metadata={"chars": len(plain)})

    def _calculator(self, tool_input: dict) -> ToolResult:
        expression = str(tool_input.get("expression") or "").strip()
        if not expression or not re.fullmatch(r"[0-9\s\+\-\*\/\(\)\.]+", expression):
            raise ToolError("calculator only supports simple arithmetic expressions.")
        try:
            result = eval(expression, {"__builtins__": {}}, {})  # noqa: S307
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"calculator failed: {exc}") from exc
        return ToolResult(name="calculator", output=str(result), metadata={"expression": expression})

    def _table_preview(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        lines = [line for line in text.splitlines() if line.strip()][:5]
        return ToolResult(name="table_preview", output=json.dumps({"rows": lines}, ensure_ascii=False), metadata={"rows": len(lines)})

    def _query_inspector(self, tool_input: dict) -> ToolResult:
        query = str(tool_input.get("query") or "").strip()
        statement = query.split(maxsplit=1)[0].lower() if query else ""
        payload = {"statement": statement, "is_read_only": statement in {"select", "with"}}
        return ToolResult(name="query_inspector", output=json.dumps(payload), metadata=payload)

    def _json_keys(self, tool_input: dict) -> ToolResult:
        value = tool_input.get("value")
        if isinstance(value, str):
            value = json.loads(value)
        if not isinstance(value, dict):
            raise ToolError("json_keys requires a JSON object.")
        keys = list(value.keys())
        return ToolResult(name="json_keys", output=json.dumps({"keys": keys}), metadata={"count": len(keys)})

    def _text_trim(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        max_chars = min(int(tool_input.get("max_chars") or 500), 10000)
        return ToolResult(name="text_trim", output=text[:max_chars], metadata={"chars": min(len(text), max_chars)})

    def _keyword_extract(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "").lower()
        words = [word for word in re.findall(r"[a-z0-9]{4,}", text) if word not in {"this", "that", "with", "from", "have", "your", "about"}]
        counts: dict[str, int] = {}
        for word in words:
            counts[word] = counts.get(word, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:15]
        return ToolResult(name="keyword_extract", output=json.dumps({"keywords": ranked}), metadata={"count": len(ranked)})

    def _reading_time(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        words = len(re.findall(r"\S+", text))
        minutes = max(1, round(words / 200))
        return ToolResult(name="reading_time", output=json.dumps({"words": words, "minutes": minutes}), metadata={"minutes": minutes})

    def _sentence_split(self, tool_input: dict) -> ToolResult:
        text = str(tool_input.get("text") or "")
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        return ToolResult(name="sentence_split", output=json.dumps({"sentences": sentences}, ensure_ascii=False), metadata={"count": len(sentences)})

    def _list_files(self, tool_input: dict) -> ToolResult:
        return self._directory_map({"path": tool_input.get("path") or "."})

    def _path_exists(self, tool_input: dict) -> ToolResult:
        path = Path(str(tool_input.get("path") or "")).expanduser()
        payload = {"path": str(path), "exists": path.exists(), "is_file": path.is_file(), "is_dir": path.is_dir()}
        return ToolResult(name="path_exists", output=json.dumps(payload), metadata=payload)

    def _mime_guess(self, tool_input: dict) -> ToolResult:
        path = Path(str(tool_input.get("path") or "")).expanduser()
        suffix = path.suffix.lower()
        guessed = {
            ".py": "text/x-python",
            ".md": "text/markdown",
            ".json": "application/json",
            ".csv": "text/csv",
            ".pdf": "application/pdf",
            ".html": "text/html",
        }.get(suffix, "application/octet-stream")
        payload = {"path": str(path), "mime_type": guessed}
        return ToolResult(name="mime_guess", output=json.dumps(payload), metadata=payload)

    def _search_memory_hints(self, tool_input: dict) -> ToolResult:
        query = str(tool_input.get("query") or "")
        tokens = [word for word in re.findall(r"[A-Za-z0-9_-]{4,}", query.lower())][:12]
        hints = [{"query": query, "hint": token} for token in tokens]
        return ToolResult(name="search_memory_hints", output=json.dumps({"hints": hints}, ensure_ascii=False), metadata={"count": len(hints)})

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
