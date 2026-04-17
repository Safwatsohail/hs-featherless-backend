from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Skill


@dataclass(frozen=True)
class BuiltinSkillDefinition:
    name: str
    description: str
    version: str
    triggers: list[str]
    when_to_use: str
    argument_hint: str | None
    prompt_template: str
    tool_permissions: list[str]
    memory_rules: dict


BUILTIN_SKILLS: list[BuiltinSkillDefinition] = [
    BuiltinSkillDefinition(
        name="default",
        description="General assistant fallback for requests that do not map to a specialized skill.",
        version="1.0.0",
        triggers=[],
        when_to_use="Use for broad requests that do not clearly match a specialized skill.",
        argument_hint=None,
        prompt_template=(
            "You are the default assistant skill.\n"
            "Answer clearly, stay within the user request, and use provided memory only when relevant.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=[],
        memory_rules={
            "short_term": True,
            "vector_store": True,
            "structured": True,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="summarize",
        description="Summarize text, notes, threads, or documents into concise structured output.",
        version="1.0.0",
        triggers=["summarize", "summary", "tl;dr", "recap"],
        when_to_use="Use when the request asks for a concise recap, summary, digest, or distilled key points.",
        argument_hint=None,
        prompt_template=(
            "You are the summarize skill.\n"
            "Produce a concise summary with key points, decisions, and next actions when present.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=[],
        memory_rules={
            "short_term": True,
            "vector_store": False,
            "structured": False,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="research",
        description="Research a topic using web search when the answer benefits from external lookup.",
        version="1.0.0",
        triggers=["research", "look up", "find", "search", "latest"],
        when_to_use="Use for factual lookup, latest information, comparisons, or external-topic research.",
        argument_hint=None,
        prompt_template=(
            "You are the research skill.\n"
            "If tool results are available, synthesize them into a direct answer with brief supporting points.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=["web_search", "url_fetch"],
        memory_rules={
            "short_term": True,
            "vector_store": True,
            "structured": True,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="code_assistant",
        description="Explain, review, or generate code and technical implementation guidance.",
        version="1.0.0",
        triggers=["code", "function", "bug", "refactor", "debug", "implement"],
        when_to_use="Use for coding, implementation advice, refactors, architecture questions, and technical explanation.",
        argument_hint=None,
        prompt_template=(
            "You are the code_assistant skill.\n"
            "Prefer precise technical output, include assumptions, and keep explanations compact.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=["python", "code_analyze"],
        memory_rules={
            "short_term": True,
            "vector_store": True,
            "structured": True,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="sql_assistant",
        description="Help with SQL analysis, safe read-only data questions, and query drafting.",
        version="1.0.0",
        triggers=["sql", "query", "database", "table", "postgres"],
        when_to_use="Use for SQL drafting, schema reasoning, query explanation, and read-only database questions.",
        argument_hint=None,
        prompt_template=(
            "You are the sql_assistant skill.\n"
            "Prefer safe, read-only analysis. Use SQL results when they are provided.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=["db_query"],
        memory_rules={
            "short_term": True,
            "vector_store": False,
            "structured": True,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="debug",
        description="Debug runtime failures, broken flows, failing tests, and root-cause analysis tasks.",
        version="1.0.0",
        triggers=["error", "failing", "failure", "broken", "traceback", "stack trace", "why is this not working"],
        when_to_use="Use when the user is troubleshooting an error, regression, failing behavior, or root cause.",
        argument_hint=None,
        prompt_template=(
            "You are the debug skill.\n"
            "Prioritize root cause, reproduction clues, and targeted fixes. If tool output exists, treat it as evidence.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=["python", "code_analyze"],
        memory_rules={
            "short_term": True,
            "vector_store": True,
            "structured": True,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline", "preferred_effort": "high"},
        },
    ),
    BuiltinSkillDefinition(
        name="explain",
        description="Teach or explain a concept, system, API, or code path clearly for humans.",
        version="1.0.0",
        triggers=["explain", "how does", "teach me", "walk me through"],
        when_to_use="Use when the user wants understanding, onboarding help, or a concept broken down clearly.",
        argument_hint=None,
        prompt_template=(
            "You are the explain skill.\n"
            "Explain clearly, step by step, with simple structure and concrete examples when useful.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=[],
        memory_rules={
            "short_term": True,
            "vector_store": False,
            "structured": False,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="review",
        description="Review content, code, or plans for bugs, risks, inconsistencies, and missing pieces.",
        version="1.0.0",
        triggers=["review", "audit", "check this", "look for issues"],
        when_to_use="Use when the user wants critical review, risk finding, bug spotting, or quality evaluation.",
        argument_hint=None,
        prompt_template=(
            "You are the review skill.\n"
            "Focus on findings first. Prioritize bugs, risks, regressions, and missing validation.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=[],
        memory_rules={
            "short_term": True,
            "vector_store": True,
            "structured": True,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline", "preferred_effort": "high"},
        },
    ),
    BuiltinSkillDefinition(
        name="planner",
        description="Turn a goal into a clear execution plan, task list, or next-step sequence.",
        version="1.0.0",
        triggers=["plan", "roadmap", "steps", "next steps", "break this down"],
        when_to_use="Use when the user wants decomposition, sequencing, milestones, or an execution plan.",
        argument_hint=None,
        prompt_template=(
            "You are the planner skill.\n"
            "Return a concrete, ordered plan with dependencies, assumptions, and the smallest useful next step.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=[],
        memory_rules={
            "short_term": True,
            "vector_store": False,
            "structured": True,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="extract",
        description="Extract structured data, entities, requirements, or fields from unstructured input.",
        version="1.0.0",
        triggers=["extract", "pull out", "parse", "identify fields", "structured data"],
        when_to_use="Use when the user needs information pulled from messy text into a clean structured form.",
        argument_hint=None,
        prompt_template=(
            "You are the extract skill.\n"
            "Extract the requested fields with high precision. Prefer explicit data over guesses.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=[],
        memory_rules={
            "short_term": True,
            "vector_store": False,
            "structured": False,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="writer",
        description="Draft polished text such as emails, docs, posts, prompts, or product copy.",
        version="1.0.0",
        triggers=["write", "draft", "rewrite", "improve wording", "compose"],
        when_to_use="Use when the user needs written content generated, rewritten, or polished for communication.",
        argument_hint=None,
        prompt_template=(
            "You are the writer skill.\n"
            "Write clean, audience-aware text. Keep the output aligned with the requested tone and format.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=[],
        memory_rules={
            "short_term": True,
            "vector_store": True,
            "structured": False,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="deep_research",
        description="Perform source-backed web research by searching, fetching pages, and synthesizing evidence.",
        version="1.0.0",
        triggers=["deep research", "investigate deeply", "comprehensive research", "analyze sources"],
        when_to_use="Use for multi-source research where search results alone are insufficient and fetched pages should be inspected.",
        argument_hint=None,
        prompt_template=(
            "You are the deep_research skill.\n"
            "Use search evidence and fetched pages to answer with concise conclusions and cited sources.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=["deep_search", "url_fetch"],
        memory_rules={
            "short_term": True,
            "vector_store": True,
            "structured": True,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline", "preferred_effort": "high"},
        },
    ),
    BuiltinSkillDefinition(
        name="pdf_analyst",
        description="Analyze PDF documents, extract text, inspect metadata, and summarize document contents.",
        version="1.0.0",
        triggers=["pdf", "analyze pdf", "read pdf", "document analysis"],
        when_to_use="Use when the user provides a PDF or asks to inspect document contents, metadata, or extracted text.",
        argument_hint=None,
        prompt_template=(
            "You are the pdf_analyst skill.\n"
            "Use extracted PDF contents to answer directly, summarize accurately, and note limitations when pages are missing.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=["pdf_analyze"],
        memory_rules={
            "short_term": True,
            "vector_store": True,
            "structured": False,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="codebase_analyst",
        description="Inspect a local codebase, summarize structure, locate relevant files, and analyze implementation details.",
        version="1.0.0",
        triggers=["analyze codebase", "inspect repo", "analyze code", "find in codebase"],
        when_to_use="Use when the task requires scanning a local repository, locating files, or summarizing code structure before answering.",
        argument_hint=None,
        prompt_template=(
            "You are the codebase_analyst skill.\n"
            "Use code analysis results to explain structure, relevant files, and likely implementation paths.\n"
            "User input: {user_input}\n"
            "Memory context: {memory_context}\n"
        ),
        tool_permissions=["code_analyze"],
        memory_rules={
            "short_term": True,
            "vector_store": True,
            "structured": True,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "auto", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="api-orchestration-standards",
        description="Hidden background knowledge for provider-agnostic AI orchestration behavior.",
        version="1.0.0",
        triggers=[],
        when_to_use="Use as hidden background guidance for this backend's orchestration, centralized memory, and provider routing.",
        argument_hint=None,
        prompt_template=(
            "Platform rules:\n"
            "- Treat upstream providers as interchangeable execution backends.\n"
            "- Use the small decision model for routing and tool planning where possible.\n"
            "- Reuse centralized memory via memory_scope and context_key.\n"
            "- Prefer compact prompts and deterministic tool usage.\n"
        ),
        tool_permissions=[],
        memory_rules={
            "short_term": False,
            "vector_store": False,
            "structured": False,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "hidden", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="safe-workflow-rules",
        description="Hidden safety rules for side-effecting workflow skills.",
        version="1.0.0",
        triggers=[],
        when_to_use="Use as hidden background guidance for manual workflow skills that can run commands or modify state.",
        argument_hint=None,
        prompt_template=(
            "Workflow safety rules:\n"
            "- Execute only commands allowed by the active skill's tool rules.\n"
            "- Refuse the workflow when required arguments are missing.\n"
            "- Report what was run and why.\n"
        ),
        tool_permissions=[],
        memory_rules={
            "short_term": False,
            "vector_store": False,
            "structured": False,
            "compose": [],
            "builtin": True,
            "_skill_config": {"invocation_mode": "hidden", "context_mode": "inline"},
        },
    ),
    BuiltinSkillDefinition(
        name="commit",
        description="Manual workflow skill to create a git commit with a provided message.",
        version="1.0.0",
        triggers=["commit"],
        when_to_use="Use only when the user explicitly wants a git commit to be created.",
        argument_hint="[commit-message]",
        prompt_template=(
            "You are the commit workflow skill.\n"
            "Use the provided arguments as the commit message: {skill_arguments}\n"
            "1. Inspect git status.\n"
            "2. Stage tracked changes that belong in this commit.\n"
            "3. Create a commit with the provided message.\n"
            "4. Return the commit summary.\n"
        ),
        tool_permissions=["bash"],
        memory_rules={
            "short_term": True,
            "vector_store": False,
            "structured": True,
            "compose": ["safe-workflow-rules"],
            "builtin": True,
            "_skill_config": {
                "invocation_mode": "manual",
                "context_mode": "fork",
                "argument_hint": "[commit-message]",
                "tool_rules": {"bash": {"command_prefixes": ["git status", "git add ", "git commit "]}},
            },
        },
    ),
    BuiltinSkillDefinition(
        name="deploy",
        description="Manual workflow skill to run a bounded deployment command for a target.",
        version="1.0.0",
        triggers=["deploy"],
        when_to_use="Use only when the user explicitly requests a deployment action.",
        argument_hint="[target-or-command]",
        prompt_template=(
            "You are the deploy workflow skill.\n"
            "Use the provided arguments to decide the approved deployment command: {skill_arguments}\n"
            "1. Inspect repository status.\n"
            "2. Run one approved deployment command.\n"
            "3. Return a concise deployment result.\n"
        ),
        tool_permissions=["bash"],
        memory_rules={
            "short_term": True,
            "vector_store": False,
            "structured": True,
            "compose": ["safe-workflow-rules", "api-orchestration-standards"],
            "builtin": True,
            "_skill_config": {
                "invocation_mode": "manual",
                "context_mode": "fork",
                "argument_hint": "[target-or-command]",
                "tool_rules": {
                    "bash": {
                        "command_prefixes": ["git status", "npm run deploy", "pnpm deploy", "yarn deploy"]
                    }
                },
            },
        },
    ),
    BuiltinSkillDefinition(
        name="issue-fix",
        description="Manual workflow skill to investigate and fix a named issue or bug.",
        version="1.0.0",
        triggers=["fix issue", "issue fix"],
        when_to_use="Use only when the user explicitly asks to work on a specific issue or bug ticket.",
        argument_hint="[issue-id-or-summary]",
        prompt_template=(
            "You are the issue-fix workflow skill.\n"
            "Investigate and fix the issue described here: {skill_arguments}\n"
            "1. Restate the issue.\n"
            "2. Inspect relevant code and evidence.\n"
            "3. Use tools if needed.\n"
            "4. Return the fix or the most likely next action.\n"
        ),
        tool_permissions=["bash", "python", "web_search"],
        memory_rules={
            "short_term": True,
            "vector_store": True,
            "structured": True,
            "compose": ["safe-workflow-rules", "api-orchestration-standards"],
            "builtin": True,
            "_skill_config": {
                "invocation_mode": "manual",
                "context_mode": "fork",
                "argument_hint": "[issue-id-or-summary]",
                "preferred_effort": "high",
                "tool_rules": {
                    "bash": {
                        "command_prefixes": ["git status", "pytest", "npm test", "pnpm test", "yarn test"]
                    }
                },
            },
        },
    ),
]


class SkillEngine:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_skill(self, skill: Skill) -> Skill:
        self.session.add(skill)
        await self.session.commit()
        await self.session.refresh(skill)
        return skill

    async def ensure_default_skill(self) -> None:
        await self.ensure_builtin_skills()

    async def ensure_builtin_skills(self) -> None:
        existing = {skill.name: skill for skill in await self.list_skills()}
        created = False
        for definition in BUILTIN_SKILLS:
            if definition.name in existing:
                continue
            self.session.add(
                Skill(
                    name=definition.name,
                    description=definition.description,
                    version=definition.version,
                    triggers=definition.triggers,
                    prompt_template=definition.prompt_template,
                    tool_permissions=definition.tool_permissions,
                    memory_rules={
                        **definition.memory_rules,
                        "_skill_config": {
                            **definition.memory_rules.get("_skill_config", {}),
                            "when_to_use": definition.when_to_use,
                            "argument_hint": definition.argument_hint,
                        },
                    },
                )
            )
            created = True
        if created:
            await self.session.commit()

    async def list_skills(self) -> list[Skill]:
        result = await self.session.execute(
            select(Skill).order_by(Skill.name.asc(), Skill.version.desc())
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Skill | None:
        result = await self.session.execute(select(Skill).where(Skill.name == name))
        return result.scalar_one_or_none()

    def get_skill_config(self, skill: Skill) -> dict:
        rules = skill.memory_rules or {}
        return dict(rules.get("_skill_config") or {})

    def get_skill_catalog(self, skills: list[Skill]) -> list[dict]:
        catalog = []
        for skill in skills:
            config = self.get_skill_config(skill)
            if config.get("invocation_mode") in {"manual", "hidden"}:
                continue
            catalog.append(
                {
                    "name": skill.name,
                    "description": skill.description,
                    "when_to_use": config.get("when_to_use"),
                    "tool_permissions": skill.tool_permissions or [],
                }
            )
        return catalog

    async def select_skill(self, *, user_input: str, skill_name: str | None = None) -> Skill:
        await self.ensure_builtin_skills()
        if skill_name:
            skill = await self.get_by_name(skill_name)
            if skill is None:
                raise ValueError(f"Unknown skill '{skill_name}'. Use GET /skills to see available skills.")
            if self.get_skill_config(skill).get("invocation_mode") == "hidden":
                raise ValueError(f"Skill '{skill_name}' is hidden and cannot be invoked directly.")
            return skill

        matched = await self.match_skill(user_input)
        if matched is not None:
            return matched

        default_skill = await self.get_by_name("default")
        if default_skill is None:
            raise ValueError("Default skill is not configured.")
        return default_skill

    async def match_skill(self, user_input: str) -> Skill | None:
        normalized = user_input.strip().lower()
        skills = await self.list_skills()

        exact_matches: list[Skill] = []
        fuzzy_matches: list[Skill] = []

        for skill in skills:
            triggers = [trigger.lower() for trigger in skill.triggers]
            if normalized in triggers:
                exact_matches.append(skill)
                continue

            if any(trigger in normalized for trigger in triggers):
                fuzzy_matches.append(skill)

        if exact_matches:
            return self._choose_highest_version(exact_matches)
        if fuzzy_matches:
            return self._choose_highest_version(fuzzy_matches)
        return None

    async def expand_composed_prompts(self, base_skill: Skill) -> str:
        memory_rules = base_skill.memory_rules or {}
        composed_names = memory_rules.get("compose") or []
        if not composed_names:
            return base_skill.prompt_template

        parts = [base_skill.prompt_template]
        for name in composed_names:
            if not name or name == base_skill.name:
                continue
            child = await self.get_by_name(str(name))
            if child is None:
                continue
            parts.append(f"\n\nComposed skill {child.name}:\n{child.prompt_template}")
        return "".join(parts)

    def execute_skill(self, skill: Skill, *, user_input: str, memory_context: str) -> str:
        config = self.get_skill_config(skill)
        return skill.prompt_template.format(
            user_input=user_input,
            memory_context=memory_context or "No relevant memories.",
            skill_name=skill.name,
            tool_permissions=", ".join(skill.tool_permissions) or "none",
            skill_arguments=config.get("active_arguments", ""),
        )

    @staticmethod
    def _choose_highest_version(skills: Iterable[Skill]) -> Skill:
        return sorted(
            skills,
            key=lambda item: tuple(int(part) for part in item.version.split(".")),
            reverse=True,
        )[0]
