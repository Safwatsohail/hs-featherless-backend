from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.skill import Skill
from backend.app.schemas.skill import SkillImportRequest, SkillImportResult
from backend.app.services.skill_engine import SkillEngine


class SkillImportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.engine = SkillEngine(session)

    async def import_skills(self, payload: SkillImportRequest) -> SkillImportResult:
        if payload.mode == "git":
            return await self._import_git_repo(payload)
        return await self._import_from_directory(
            root=Path(payload.source).expanduser(),
            prefix=payload.prefix,
            invocation_mode=payload.invocation_mode,
            overwrite=payload.overwrite,
        )

    async def _import_git_repo(self, payload: SkillImportRequest) -> SkillImportResult:
        with tempfile.TemporaryDirectory(prefix="skill_repo_") as td:
            target = Path(td) / "repo"
            subprocess.run(
                ["git", "clone", "--depth", "1", payload.source, str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
            return await self._import_from_directory(
                root=target,
                prefix=payload.prefix,
                invocation_mode=payload.invocation_mode,
                overwrite=payload.overwrite,
            )

    async def _import_from_directory(
        self,
        *,
        root: Path,
        prefix: str | None,
        invocation_mode: str | None,
        overwrite: bool,
    ) -> SkillImportResult:
        result = SkillImportResult()
        if not root.exists():
            result.errors.append(f"Path does not exist: {root}")
            return result

        skill_files = self._discover_skill_files(root)
        if not skill_files:
            result.errors.append(f"No SKILL.md files found under: {root}")
            return result

        for skill_file in skill_files:
            try:
                skill = await self._build_skill_from_file(
                    skill_file=skill_file,
                    prefix=prefix,
                    invocation_mode=invocation_mode,
                )
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"{skill_file}: {exc}")
                continue

            existing = await self.engine.get_by_name(skill.name)
            if existing and not overwrite:
                result.skipped.append(skill.name)
                continue

            if existing and overwrite:
                existing.description = skill.description
                existing.version = skill.version
                existing.triggers = skill.triggers
                existing.prompt_template = skill.prompt_template
                existing.tool_permissions = skill.tool_permissions
                existing.memory_rules = skill.memory_rules
                await self.session.commit()
                result.imported.append(skill.name)
                continue

            self.session.add(skill)
            result.imported.append(skill.name)

        await self.session.commit()
        return result

    async def _build_skill_from_file(
        self,
        *,
        skill_file: Path,
        prefix: str | None,
        invocation_mode: str | None,
    ) -> Skill:
        raw = skill_file.read_text(encoding="utf-8")
        frontmatter, body = self._split_frontmatter(raw)
        data = yaml.safe_load(frontmatter) if frontmatter else {}
        if not isinstance(data, dict):
            data = {}

        name = str(data.get("name") or skill_file.parent.name).strip().lower()
        if prefix:
            name = f"{prefix}-{name}"
        description = str(data.get("description") or body.splitlines()[0] if body.strip() else name).strip()

        allowed_tools = data.get("allowed-tools") or data.get("allowed_tools") or []
        if isinstance(allowed_tools, str):
            allowed_tools = [part.strip() for part in allowed_tools.replace(",", " ").split() if part.strip()]
        mapped_tools = [self._map_tool_name(tool) for tool in allowed_tools]
        mapped_tools = [tool for tool in mapped_tools if tool]

        disable_model_invocation = bool(
            data.get("disable-model-invocation") or data.get("disable_model_invocation")
        )
        config_invocation_mode = invocation_mode or ("manual" if disable_model_invocation else "auto")

        return Skill(
            name=name[:80],
            description=description[:500],
            version="1.0.0",
            triggers=self._infer_triggers(name, description),
            prompt_template=body.strip(),
            tool_permissions=list(dict.fromkeys(mapped_tools)),
            memory_rules={
                "short_term": True,
                "vector_store": True,
                "structured": True,
                "compose": [],
                "_skill_config": {
                    "when_to_use": description,
                    "invocation_mode": config_invocation_mode,
                    "context_mode": "inline",
                    "source_kind": "claude_skill",
                    "source_path": str(skill_file),
                },
            },
        )

    @staticmethod
    def _discover_skill_files(root: Path) -> list[Path]:
        candidates = list(root.rglob("SKILL.md"))
        if candidates:
            return sorted(candidates)
        return sorted(root.rglob("*.md"))

    @staticmethod
    def _split_frontmatter(raw: str) -> tuple[str, str]:
        if not raw.startswith("---\n"):
            return "", raw
        parts = raw.split("\n---\n", 1)
        if len(parts) != 2:
            return "", raw
        return parts[0].removeprefix("---\n"), parts[1]

    @staticmethod
    def _infer_triggers(name: str, description: str) -> list[str]:
        pieces = [name.replace("-", " ")]
        for token in description.split("."):
            token = token.strip().lower()
            if 0 < len(token) <= 80:
                pieces.append(token)
            if len(pieces) >= 5:
                break
        return list(dict.fromkeys(pieces))

    @staticmethod
    def _map_tool_name(name: str) -> str | None:
        normalized = str(name).strip().lower()
        mapping = {
            "bash": "bash",
            "read": "code_analyze",
            "grep": "code_analyze",
            "glob": "code_analyze",
            "webfetch": "url_fetch",
            "web-search": "web_search",
            "web_search": "web_search",
            "search": "web_search",
            "pdf": "pdf_analyze",
        }
        return mapping.get(normalized)
