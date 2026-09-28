"""Application operations for creating, cancelling, and deleting projects."""

import uuid

from service.background_runtime import background_queue
from service.errors import ServiceError
from service.models import BulkProjectDeleteRequest, ProjectGenerationRequest, ProjectJob
from service.storage.database import database
from service.storage.file_store import file_store
from service.storage.job_store import job_store


async def create_job(generation_request: ProjectGenerationRequest) -> ProjectJob:
    job = ProjectJob(
        id=str(uuid.uuid4()),
        request=generation_request,
        provider=generation_request.provider,
    )
    await database.save_job(job)
    await background_queue.enqueue_job(job.id)
    return job


async def delete_and_files(id: str) -> bool:
    job = await job_store.get_job(id)
    if not job:
        return False

    await background_queue.cancel_job(id)
    file_store.delete_folder(id)
    return await job_store.delete_job(id)


async def cancel_job(id: str):
    job = await job_store.get_job(id)
    if not job:
        raise ServiceError(404, "Project not found")
    if job.status.value == "cancelled":
        return {"ok": True, "project_id": id, "status": "cancelled", "already_cancelled": True}
    if job.status.value not in ("queued", "running"):
        raise ServiceError(409, f"Project is already {job.status.value} and cannot be stopped")

    await background_queue.cancel_job(id)
    cancelled = await job_store.cancel_job(id)
    if not cancelled:
        latest_job = await job_store.get_job(id)
        if latest_job and latest_job.status.value == "cancelled":
            return {"ok": True, "project_id": id, "status": "cancelled", "already_cancelled": True}
        latest_status = latest_job.status.value if latest_job else "missing"
        raise ServiceError(409, f"Project became {latest_status} before it could be stopped")

    return {"ok": True, "project_id": id, "status": "cancelled"}


async def delete_jobs_bulk(delete_request: BulkProjectDeleteRequest):
    if delete_request.confirm != "Delete":
        raise ServiceError(400, "Type Delete exactly to confirm project deletion")

    deleted_ids = []
    missing_ids = []
    for id in delete_request.ids:
        if await delete_and_files(id):
            deleted_ids.append(id)
        else:
            missing_ids.append(id)

    return {
        "ok": True,
        "deleted_project_ids": deleted_ids,
        "missing_project_ids": missing_ids,
    }
