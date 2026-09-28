import asyncio
from contextlib import suppress
from core.config import settings
from storage.database import database
from storage.jobs import job_store


class ProjectQueue:
    def __init__(self):
        self.queue=asyncio.Queue()
        self.workers=[]
        self.running=set()
        self.pending=set()
        self.active_tasks={}
        self.cancelled=set()
        self._started=False

    async def start(self, executor):
        if self._started:
            return
        self._started=True

        await database.mark_running_as_queued()
        queued=await database.list_jobs(limit=1000,status="queued")
        for job in reversed(queued):
            self.pending.add(job.id)
            await self.queue.put(job.id)

        for i in range(settings.max_concurrent_projects):
            self.workers.append(asyncio.create_task(
                self._worker(executor,i),
                name=f"content-factory-worker-{i}"
            ))

    async def _worker(self, executor, worker_id):
        while True:
            job_id=await self.queue.get()
            self.pending.discard(job_id)
            try:
                if job_id in self.cancelled:
                    self.cancelled.discard(job_id)
                    continue
                job=await job_store.get(job_id)
                if not job or job.status.value=="cancelled":
                    continue
                self.running.add(job_id)
                task=asyncio.create_task(executor(job),name=f"project-{job_id}")
                self.active_tasks[job_id]=task
                try:
                    await task
                except asyncio.CancelledError:
                    # Per-project cancellation must not kill the worker itself.
                    if job_id not in self.cancelled:
                        raise
            finally:
                self.active_tasks.pop(job_id,None)
                self.running.discard(job_id)
                self.queue.task_done()

    async def submit(self,job_id):
        self.cancelled.discard(job_id)
        self.pending.add(job_id)
        await self.queue.put(job_id)

    async def cancel(self,job_id):
        """Prevent queued work from starting or stop an active project safely."""
        self.cancelled.add(job_id)
        self.pending.discard(job_id)
        task=self.active_tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        self.running.discard(job_id)
        if task:
            self.cancelled.discard(job_id)
        return True

    def snapshot(self):
        return {
            "max_concurrent":settings.max_concurrent_projects,
            "running_count":len(self.running),
            "running_ids":sorted(self.running),
            # asyncio.Queue may still contain cancelled tombstones until a worker
            # dequeues them. `pending` reflects projects users can actually see/run.
            "queued_count":len(self.pending),
        }


project_queue=ProjectQueue()
