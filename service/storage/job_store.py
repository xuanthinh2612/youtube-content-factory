"""Compatibility facade for callers that use the job-store interface."""

from service.storage.database import database
from service.models import ProjectJob


class ProjectJobStore:
    async def save_job(self, job: ProjectJob):
        await database.save_job(job)

    async def get_job(self, job_id: str):
        return await database.get_job(job_id)

    async def list_jobs(self, limit=200, status=None):
        return await database.list_jobs(limit=limit, status=status)

    async def delete_job(self, job_id: str):
        return await database.delete_record(job_id)

    async def cancel_job(self, job_id: str):
        return await database.cancel_job(job_id)


job_store=ProjectJobStore()
