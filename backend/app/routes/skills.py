from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.models.skill import Skill
from backend.app.schemas.skill import SkillCreate, SkillImportRequest, SkillImportResult, SkillResponse
from backend.app.services.skill_importer import SkillImportService
from backend.app.services.skill_engine import SkillEngine

router = APIRouter(prefix="/skills", tags=["skills"])


def _build_skill_response(engine: SkillEngine, skill: Skill) -> SkillResponse:
    config = engine.get_skill_config(skill)
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        version=skill.version,
        triggers=skill.triggers or [],
        when_to_use=config.get("when_to_use"),
        argument_hint=config.get("argument_hint"),
        prompt_template=skill.prompt_template,
        tool_permissions=skill.tool_permissions or [],
        memory_rules=skill.memory_rules or {},
        is_builtin=bool((skill.memory_rules or {}).get("builtin")),
        invocation_mode=config.get("invocation_mode", "auto"),
        context_mode=config.get("context_mode", "inline"),
        preferred_model=config.get("preferred_model"),
        preferred_effort=config.get("preferred_effort"),
        tool_rules=config.get("tool_rules", {}),
    )


@router.get("", response_model=list[SkillResponse])
async def list_skills(db: AsyncSession = Depends(get_db)) -> list[SkillResponse]:
    engine = SkillEngine(db)
    await engine.ensure_builtin_skills()
    skills = await engine.list_skills()
    visible_skills = [
        skill for skill in skills if engine.get_skill_config(skill).get("invocation_mode") != "hidden"
    ]
    return [_build_skill_response(engine, skill) for skill in visible_skills]


@router.post("", response_model=SkillResponse)
async def create_skill(payload: SkillCreate, db: AsyncSession = Depends(get_db)) -> SkillResponse:
    engine = SkillEngine(db)
    skill = Skill(
        name=payload.name,
        description=payload.description,
        version=payload.version,
        triggers=payload.triggers,
        prompt_template=payload.prompt_template,
        tool_permissions=payload.tool_permissions,
        memory_rules={
            **payload.memory_rules.model_dump(),
            "_skill_config": {
                "when_to_use": payload.when_to_use,
                "argument_hint": payload.argument_hint,
                "invocation_mode": payload.invocation_mode,
                "context_mode": payload.context_mode,
                "preferred_model": payload.preferred_model,
                "preferred_effort": payload.preferred_effort,
                "tool_rules": payload.tool_rules,
            },
        },
    )
    created = await engine.create_skill(skill)
    return _build_skill_response(engine, created)


@router.post("/import", response_model=SkillImportResult)
async def import_skills(payload: SkillImportRequest, db: AsyncSession = Depends(get_db)) -> SkillImportResult:
    importer = SkillImportService(db)
    return await importer.import_skills(payload)
