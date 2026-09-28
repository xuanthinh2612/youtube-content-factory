"""Coordinate the Director, Writer, reviewer, and Editor for each language."""

import json

from service.agents.role_execution import reviewer, director, editor, writer
from service.models import ProjectJob


def split_generated_title(content, fallback_title):
    """Separate an Editor's Markdown H1 from the body for display and export."""
    lines = str(content or "").splitlines()
    first_content_line = next((index for index, line in enumerate(lines) if line.strip()), None)
    if first_content_line is None:
        return fallback_title, ""

    first_line = lines[first_content_line].strip()
    if first_line.startswith("# "):
        title = first_line[2:].strip().strip("# ")
        body = "\n".join(lines[first_content_line + 1:]).lstrip()
        return title or fallback_title, body

    return fallback_title, str(content or "").strip()


def get_director_title(director_outline):
    """Read the canonical title from the Director's JSON response."""
    try:
        outline_data = json.loads(director_outline)
    except (TypeError, json.JSONDecodeError) as error:
        raise RuntimeError("DIRECTOR_OUTLINE_INVALID_JSON") from error

    if not isinstance(outline_data, dict):
        raise RuntimeError("DIRECTOR_OUTLINE_INVALID_JSON")
    title = str(outline_data.get("title") or "").strip()
    if not title:
        raise RuntimeError("DIRECTOR_TITLE_MISSING")
    return title


class ContentGenerationWorkflow:
    async def generate_for_project(
        self,
        job: ProjectJob,
        save_language_output=None,
    ):
        generated_title = ""
        for language in job.request.languages:
            director_outline = await director(job, language)
            writer_output = await writer(job, language, director_outline)
            reviewer_feedback = await reviewer(
                job, language, director_outline, writer_output
            )
            final_result = await editor(
                job,
                language,
                writer_output,
                reviewer_feedback,
            )
            title = get_director_title(director_outline)
            _, final_content = split_generated_title(final_result, title)
            if not generated_title:
                generated_title = title

            completed_language_output = {
                "title": title,
                "outline": {
                    "content_type": job.request.niche,
                    "director_plan": director_outline,
                },
                "final_text": final_content,
            }
            if save_language_output:
                await save_language_output(
                    language,
                    completed_language_output,
                )

        return generated_title or job.request.user_promt[:96]


content_generation_workflow = ContentGenerationWorkflow()


async def run_content_generation(
    job: ProjectJob,
    save_language_output=None,
):
    return await content_generation_workflow.generate_for_project(
        job,
        save_language_output=save_language_output,
    )
