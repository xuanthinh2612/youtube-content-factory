"""Run a project through content generation, export, and final status updates."""

from service.exporters.content_exporter import write_content_files
from service.observability.activity import activity_context, activity_logger
from service.models import ProjectJob, ProjectStatus, utc_timestamp
from service.storage.database import database
from service.storage.file_store import file_store
from service.workflows.content_generation import run_content_generation


def build_display_name(agent_returned_name, requested_user_promt):
    display_name = " ".join(str(agent_returned_name or "").split()).strip(" -–—:;, .\t\n")
    if not display_name:
        user_promt_words = " ".join(str(requested_user_promt or "").split()).split()
        display_name = " ".join(user_promt_words[:8]) or "Untitled project"
    return display_name[:96]


async def run_pipeline(job: ProjectJob):
    completed_language_outputs = {}
    latest_director_outline = {}

    def build_export_data():
        exported_title = next(
            (output.get("title") for output in completed_language_outputs.values() if output.get("title")),
            job.name or job.request.user_promt[:96],
        )
        return {
            "title": exported_title,
            "user_promt": job.request.user_promt,
            "niche": job.request.niche,
            "blueprint": latest_director_outline,
            "outputs": {
                language: {
                    "title": language_output["title"],
                    "content": str(language_output.get("final_text") or ""),
                    "outline": language_output["outline"],
                }
                for language, language_output in completed_language_outputs.items()
            },
            **({"error": job.error} if job.error else {}),
        }

    async def save_completed_language_output(language, language_output):
        latest_director_outline.clear()
        latest_director_outline.update(language_output["outline"])
        completed_language_outputs[language] = language_output
        job.result = build_export_data()
        write_content_files(file_store.ensure_folder(job.id), job.result["title"], job.result)
        job.updated_at = utc_timestamp()
        await database.save_job(job)

    try:
        job.status = ProjectStatus.running
        job.stage = "director"
        job.progress = 2
        job.error = None
        job.started_at = utc_timestamp()
        job.updated_at = utc_timestamp()
        await database.save_job(job)

        with activity_context(job.id):
            agent_returned_name = await run_content_generation(
                job,
                save_language_output=save_completed_language_output,
            )
            job.name = build_display_name(
                agent_returned_name, job.request.user_promt
            )
            job.updated_at = utc_timestamp()
            await database.save_job(job)

            job.stage = "export"
            job.progress = 90
            job.updated_at = utc_timestamp()
            await database.save_job(job)

            job.result = build_export_data()
            write_content_files(file_store.ensure_folder(job.id), agent_returned_name, job.result)

        job.stage = "completed"
        job.progress = 100
        job.status = ProjectStatus.completed
        job.completed_at = utc_timestamp()
        job.updated_at = utc_timestamp()
        await database.save_job(job)
    except Exception as generation_error:
        try:
            latest_job = await database.get_job(job.id)
        except Exception:
            latest_job = None

        failed_stage = (latest_job.stage if latest_job else job.stage) or "unknown"
        if latest_job:
            job.progress = latest_job.progress
            job.name = latest_job.name

        job.error = f"{type(generation_error).__name__}: {generation_error}"
        try:
            job.result = build_export_data()
            write_content_files(file_store.ensure_folder(job.id), job.result["title"], job.result)
        except Exception:
            pass

        job.stage = "failed"
        job.status = ProjectStatus.failed
        job.completed_at = utc_timestamp()
        job.updated_at = utc_timestamp()
        await database.save_job(job)
        await activity_logger.record_activity_event(
            {
                "type": "node_error",
                "node": failed_stage,
                "status": "failed",
                "message": job.error,
            },
            job.id,
        )
