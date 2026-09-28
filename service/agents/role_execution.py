from pathlib import Path

from service.openai_client import send_openai_response
from service.observability.activity import activity_logger
from service.agents.helper import (
    build_reviewer_role_task,
    build_director_role_task,
    build_editor_role_task,
    build_writer_role_task,
)
from service.schemas.output_schemas import (
    DIRECTOR_OUTLINE_OUTPUT_FORMATS,
)


AGENT_PROMPT_DIRECTORY = Path(__file__).resolve().parent / "prompts"


def load_role_instructions(niche, agent_role):
    path = AGENT_PROMPT_DIRECTORY / f"{niche}_{agent_role}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"No prompt configured for domain={niche!r}, role={agent_role!r}"
        )
    return path.read_text(encoding="utf-8")


def build_role_input(job, language):
    request = job.request
    parts = []

    def add(label, value):
        if value is not None and str(value).strip():
            parts.append(f"{label}: {value}")

    add("USER PROMPT/REQUIREMENT", request.user_promt)
    add("NICHE", request.niche)
    add("LANGUAGE", language)
    add("DURATION MINUTES", request.duration_minutes)
    add("SUB-NICHE", request.sub_niche)
    add("STYLE", request.style)
    add("TONE", request.tone)
    add("AUDIENCE", request.audience)
    add("EXTRA INSTRUCTIONS", request.extra_instructions)

    return "\n".join(parts)
    

def get_agent_output_format(niche, agent_role):
    if agent_role != "director":
        return None
    return DIRECTOR_OUTLINE_OUTPUT_FORMATS.get(niche)


async def execute_agent_role(job, language, agent_role, role_task):
    await activity_logger.record_agent_started(agent_role)
    openai_response = await send_openai_response(
        job,
        load_role_instructions(job.request.niche, agent_role),
        build_role_input(job, language) + role_task,
        output_format=get_agent_output_format(job.request.niche, agent_role),
    )
    await activity_logger.record_agent_succeeded(agent_role, openai_response.output_text, language=language)
    return openai_response.output_text


async def director(job, language):
    role_task = build_director_role_task(language)
    return await execute_agent_role(job, language, "director", role_task)


async def writer(job, language, director_outline):
    role_task = build_writer_role_task(language, director_outline)
    return await execute_agent_role(job, language, "writer", role_task)


async def reviewer(job, language, director_outline, writer_draft):
    role_task = build_reviewer_role_task(director_outline, writer_draft)
    return await execute_agent_role(job, language, "reviewer", role_task)


async def editor(job, language, writer_draft, reviewer_feedback=""):
    role_task = build_editor_role_task(language, writer_draft, reviewer_feedback)
    return await execute_agent_role(job, language, "editor", role_task)
