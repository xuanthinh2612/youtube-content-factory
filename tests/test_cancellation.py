import asyncio
import tempfile
import unittest
from pathlib import Path

from service.settings import app_settings
from service.background_runtime import BackgroundProjectQueue
from service.models import ProjectGenerationRequest, ProjectJob, ProjectStatus
from service.storage.database import database
from service.storage.job_store import job_store


ROOT = Path(__file__).resolve().parents[1]


class ProjectCancellationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_db_path = app_settings.db_path
        app_settings.db_path = str(Path(self.temp_dir.name) / "factory.db")
        await database.initialize_database()

    async def asyncTearDown(self):
        app_settings.db_path = self.old_db_path
        self.temp_dir.cleanup()

    @staticmethod
    def job(job_id: str, status: ProjectStatus = ProjectStatus.queued) -> ProjectJob:
        return ProjectJob(
            id=job_id,
            request=ProjectGenerationRequest(user_promt="A cancellation test topic", niche="story"),
            status=status,
            stage=status.value,
            progress=42,
        )

    async def test_database_cancels_only_queued_or_running_projects(self):
        queued = self.job("queued-project")
        running = self.job("running-project", ProjectStatus.running)
        completed = self.job("completed-project", ProjectStatus.completed)
        for job in (queued, running, completed):
            await job_store.save_job(job)

        self.assertTrue(await job_store.cancel_job(queued.id))
        self.assertTrue(await job_store.cancel_job(running.id))
        self.assertFalse(await job_store.cancel_job(completed.id))

        for id in (queued.id, running.id):
            stopped = await job_store.get_job(id)
            self.assertEqual(stopped.status, ProjectStatus.cancelled)
            self.assertEqual(stopped.stage, "cancelled")
            self.assertIsNotNone(stopped.completed_at)
            self.assertIsNone(stopped.error)

        untouched = await job_store.get_job(completed.id)
        self.assertEqual(untouched.status, ProjectStatus.completed)

    async def test_queue_cancels_active_task_without_cancelling_worker(self):
        queue = BackgroundProjectQueue()
        started = asyncio.Event()

        async def active_work():
            started.set()
            await asyncio.Event().wait()

        role_task = asyncio.create_task(active_work())
        queue.active_tasks["active-project"] = role_task
        queue.active_ids.add("active-project")
        await started.wait()

        await queue.cancel_job("active-project")

        self.assertTrue(role_task.cancelled())
        self.assertNotIn("active-project", queue.active_ids)
        self.assertNotIn("active-project", queue.cancelled_ids)

    async def test_queue_tombstones_pending_project(self):
        queue = BackgroundProjectQueue()
        queue.pending_ids.add("pending-project")

        await queue.cancel_job("pending-project")

        self.assertNotIn("pending-project", queue.pending_ids)
        self.assertIn("pending-project", queue.cancelled_ids)


def test_force_stop_is_exposed_by_api_and_both_views():
    api_source = (ROOT / "api" / "main.py").read_text(encoding="utf-8")
    service_source = (ROOT / "service" / "operations.py").read_text(encoding="utf-8")
    detail_source = (ROOT / "templates" / "detail.html").read_text(encoding="utf-8")
    list_source = (ROOT / "templates" / "list.html").read_text(encoding="utf-8")

    assert '@app.post("/api/projects/<job_id>/cancel")' in api_source
    assert "await background_queue.cancel_job(id)" in service_source
    assert "await job_store.cancel_job(id)" in service_source
    assert "cancel_job_from_page" in detail_source
    assert "cancel_job_from_page" in list_source
