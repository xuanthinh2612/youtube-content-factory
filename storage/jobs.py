from storage.database import database
from core.schemas.job import Job


class JobStore:
    async def put(self, job: Job):
        await database.upsert_job(job)

    async def get(self, job_id: str):
        return await database.get_job(job_id)

    async def list(self, limit=200, status=None):
        return await database.list_jobs(limit=limit, status=status)

    async def delete(self, job_id: str):
        return await database.delete_project(job_id)

    async def cancel(self, job_id: str):
        return await database.cancel_project(job_id)


job_store=JobStore()
