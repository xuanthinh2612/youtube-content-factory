"""Background project queue and asyncio runtime used by the Flask app."""

import atexit
import asyncio
import threading
from contextlib import suppress

from service.openai_client import openai_client
from service.execution import run_pipeline
from service.settings import app_settings
from service.storage.database import database


class BackgroundProjectQueue:
    """Run queued project jobs with a fixed number of async workers."""

    def __init__(self):
        self.pending_queue = asyncio.Queue()
        self.worker_tasks = []
        self.active_ids = set()
        self.pending_ids = set()
        self.active_tasks = {}
        self.cancelled_ids = set()
        self._started = False

    async def start_queue_workers(self, executor):
        if self._started:
            return
        self._started = True
        await database.requeue_interrupted_jobs()
        queued_jobs = await database.list_jobs(limit=1000, status="queued")
        for job in reversed(queued_jobs):
            self.pending_ids.add(job.id)
            await self.pending_queue.put(job.id)
        for worker_index in range(app_settings.max_concurrent_projects):
            self.worker_tasks.append(asyncio.create_task(
                self._process_queued_jobs(executor, worker_index),
                name=f"content-factory-worker-{worker_index}",
            ))

    async def _process_queued_jobs(self, executor, worker_index):
        while True:
            id = await self.pending_queue.get()
            self.pending_ids.discard(id)
            try:
                if id in self.cancelled_ids:
                    self.cancelled_ids.discard(id)
                    continue

                job = await database.get_job(id)
                if not job or job.status.value == "cancelled":
                    continue

                self.active_ids.add(id)
                task = asyncio.create_task(
                    executor(job), name=f"project-{id}"
                )
                self.active_tasks[id] = task
                try:
                    await task
                except asyncio.CancelledError:
                    if id not in self.cancelled_ids:
                        raise
            finally:
                self.active_tasks.pop(id, None)
                self.active_ids.discard(id)
                self.pending_queue.task_done()

    async def enqueue_job(self, id):
        self.cancelled_ids.discard(id)
        self.pending_ids.add(id)
        await self.pending_queue.put(id)

    async def cancel_job(self, id):
        """Prevent queued work from starting or stop an active project safely."""
        self.cancelled_ids.add(id)
        self.pending_ids.discard(id)
        task = self.active_tasks.get(id)
        if task and not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        self.active_ids.discard(id)
        if task:
            self.cancelled_ids.discard(id)
        return True

    def get_status_summary(self):
        return {
            "max_concurrent": app_settings.max_concurrent_projects,
            "running_count": len(self.active_ids),
            "running_ids": sorted(self.active_ids),
            "queued_count": len(self.pending_ids),
        }


background_queue = BackgroundProjectQueue()


class BackgroundAsyncRuntime:
    """Run project workers on a persistent asyncio loop behind Flask threads."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(
            target=self._run_background_event_loop,
            name="content-factory-async",
            daemon=True,
        )
        self.loop_ready = threading.Event()
        self.start_lock = threading.Lock()
        self.started = False

    def _run_background_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.call_soon(self.loop_ready.set)
        self.loop.run_forever()

    def start_background_runtime(self):
        with self.start_lock:
            if not self.started:
                self.thread.start()
                self.loop_ready.wait()
                self.started = True
                self.run_coroutine_on_background_loop(self.initialize_background_services())

    async def initialize_background_services(self):
        await database.initialize_database()
        await background_queue.start_queue_workers(run_pipeline)

    def run_coroutine_on_background_loop(self, coroutine, timeout=None):
        if not self.started:
            self.start_background_runtime()
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result(timeout=timeout)

    def stop_background_runtime(self):
        if self.started and self.loop.is_running():
            try:
                self.run_coroutine_on_background_loop(openai_client.close(), timeout=10)
            except Exception:
                pass
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=2)
            self.started = False


background_runtime = BackgroundAsyncRuntime()
atexit.register(background_runtime.stop_background_runtime)


def run_async_operation(coroutine, timeout=None):
    return background_runtime.run_coroutine_on_background_loop(coroutine, timeout=timeout)


async def get_queue_status():
    return background_queue.get_status_summary()
