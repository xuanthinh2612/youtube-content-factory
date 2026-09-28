import asyncio
import tempfile
import unittest
from pathlib import Path

from core.config import settings
from core.runtime import ProjectQueue
from core.schemas.job import GenerateRequest, Job, JobStatus
from core.workflow.graph_state import reduce_graph
from storage.database import database
from storage.jobs import job_store


ROOT = Path(__file__).resolve().parents[1]


class ProjectCancellationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_db_path = settings.db_path
        settings.db_path = str(Path(self.temp_dir.name) / "factory.db")
        await database.init()

    async def asyncTearDown(self):
        settings.db_path = self.old_db_path
        self.temp_dir.cleanup()

    @staticmethod
    def job(job_id: str, status: JobStatus = JobStatus.queued) -> Job:
        return Job(
            id=job_id,
            request=GenerateRequest(topic="A cancellation test topic", niche="story"),
            status=status,
            stage=status.value,
            progress=42,
        )

    async def test_database_cancels_only_queued_or_running_projects(self):
        queued = self.job("queued-project")
        running = self.job("running-project", JobStatus.running)
        completed = self.job("completed-project", JobStatus.completed)
        for job in (queued, running, completed):
            await job_store.put(job)

        self.assertTrue(await job_store.cancel(queued.id))
        self.assertTrue(await job_store.cancel(running.id))
        self.assertFalse(await job_store.cancel(completed.id))

        for project_id in (queued.id, running.id):
            stopped = await job_store.get(project_id)
            self.assertEqual(stopped.status, JobStatus.cancelled)
            self.assertEqual(stopped.stage, "cancelled")
            self.assertIsNotNone(stopped.completed_at)
            self.assertIsNone(stopped.error)

        untouched = await job_store.get(completed.id)
        self.assertEqual(untouched.status, JobStatus.completed)

    async def test_queue_cancels_active_task_without_cancelling_worker(self):
        queue = ProjectQueue()
        started = asyncio.Event()

        async def active_work():
            started.set()
            await asyncio.Event().wait()

        task = asyncio.create_task(active_work())
        queue.active_tasks["active-project"] = task
        queue.running.add("active-project")
        await started.wait()

        await queue.cancel("active-project")

        self.assertTrue(task.cancelled())
        self.assertNotIn("active-project", queue.running)
        self.assertNotIn("active-project", queue.cancelled)

    async def test_queue_tombstones_pending_project(self):
        queue = ProjectQueue()
        queue.pending.add("pending-project")

        await queue.cancel("pending-project")

        self.assertNotIn("pending-project", queue.pending)
        self.assertIn("pending-project", queue.cancelled)


def test_force_stop_is_exposed_by_api_and_both_project_views():
    api_source = (ROOT / "api" / "main.py").read_text(encoding="utf-8")
    client_source = (ROOT / "frontend" / "src" / "lib" / "api.js").read_text(encoding="utf-8")
    detail_source = (ROOT / "frontend" / "src" / "views" / "ProjectView.vue").read_text(encoding="utf-8")
    list_source = (ROOT / "frontend" / "src" / "views" / "ProjectsView.vue").read_text(encoding="utf-8")

    assert '@app.post("/api/projects/{job_id}/cancel")' in api_source
    assert "await project_queue.cancel(job_id)" in api_source
    assert "await job_store.cancel(job_id)" in api_source
    assert "cancelProject:" in client_source
    assert "Force stop" in detail_source
    assert "Force stop" in list_source


def test_cancel_event_clears_running_state_in_workflow_graph():
    spec = {
        "nodes": [{"id": "director"}, {"id": "writer"}],
        "edges": [{"source": "director", "target": "writer", "kind": "normal"}],
    }
    history = [
        {"type": "node_start", "node": "director", "status": "running"},
        {
            "type": "project_cancelled",
            "node": "cancelled",
            "status": "cancelled",
            "message": "Project force-stopped by user",
        },
    ]

    graph = reduce_graph(spec, history, "cancelled")

    statuses = {node["id"]: node["status"] for node in graph["nodes"]}
    assert statuses == {"director": "cancelled", "writer": "idle"}
