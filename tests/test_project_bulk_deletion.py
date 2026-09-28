import tempfile
import unittest
from pathlib import Path

import pytest
from fastapi import HTTPException

from core.config import settings
from core.schemas.job import BulkDeleteRequest, GenerateRequest, Job, JobStatus
from storage.database import database
from storage.files import file_store
from storage.jobs import job_store


ROOT = Path(__file__).resolve().parents[1]


class BulkDeleteProjectsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_db_path = settings.db_path
        self.old_data_dir = settings.data_dir
        self.old_base = file_store.base
        settings.db_path = str(Path(self.temp_dir.name) / "factory.db")
        settings.data_dir = self.temp_dir.name
        await database.init()
        # `file_store` is a process-wide singleton created at import time, so
        # tests must repoint its resolved base dir to the temp dir directly.
        file_store.base = Path(self.temp_dir.name).resolve()
        self.file_store = file_store

    async def asyncTearDown(self):
        settings.db_path = self.old_db_path
        settings.data_dir = self.old_data_dir
        file_store.base = self.old_base
        self.temp_dir.cleanup()

    @staticmethod
    def job(job_id: str, status: JobStatus = JobStatus.completed) -> Job:
        return Job(
            id=job_id,
            request=GenerateRequest(topic="A bulk delete test topic", niche="story"),
            status=status,
            stage=status.value,
            progress=100,
        )

    async def test_delete_projects_bulk_only_removes_selected_projects(self):
        from api.main import delete_projects_bulk

        keep = self.job("keep-project")
        remove_a = self.job("remove-a")
        remove_b = self.job("remove-b")
        for job in (keep, remove_a, remove_b):
            await job_store.put(job)
            folder = self.file_store.folder(job.id)
            (folder / "artifact.txt").write_text("generated", encoding="utf-8")

        payload = BulkDeleteRequest(project_ids=[remove_a.id, remove_b.id], confirm="Delete")
        result = await delete_projects_bulk(payload)

        self.assertEqual(sorted(result["deleted_project_ids"]), [remove_a.id, remove_b.id])
        self.assertEqual(result["missing_project_ids"], [])

        self.assertIsNone(await job_store.get(remove_a.id))
        self.assertIsNone(await job_store.get(remove_b.id))
        self.assertFalse(self.file_store.path(remove_a.id).exists())
        self.assertFalse(self.file_store.path(remove_b.id).exists())

        untouched = await job_store.get(keep.id)
        self.assertIsNotNone(untouched)
        self.assertTrue(self.file_store.path(keep.id).exists())

    async def test_delete_projects_bulk_reports_missing_ids_without_failing(self):
        from api.main import delete_projects_bulk

        existing = self.job("existing-project")
        await job_store.put(existing)

        payload = BulkDeleteRequest(project_ids=[existing.id, "never-created"], confirm="Delete")
        result = await delete_projects_bulk(payload)

        self.assertEqual(result["deleted_project_ids"], [existing.id])
        self.assertEqual(result["missing_project_ids"], ["never-created"])

    async def test_delete_projects_bulk_rejects_wrong_confirmation(self):
        from api.main import delete_projects_bulk

        existing = self.job("existing-project")
        await job_store.put(existing)

        payload = BulkDeleteRequest(project_ids=[existing.id], confirm="delete")
        with self.assertRaises(HTTPException) as ctx:
            await delete_projects_bulk(payload)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIsNotNone(await job_store.get(existing.id))


def test_bulk_delete_request_rejects_invalid_project_ids():
    with pytest.raises(Exception):
        BulkDeleteRequest(project_ids=["../etc"], confirm="Delete")
    with pytest.raises(Exception):
        BulkDeleteRequest(project_ids=[], confirm="Delete")


def test_bulk_delete_endpoint_reuses_single_delete_semantics():
    source = (ROOT / "api/main.py").read_text(encoding="utf-8")
    assert '@app.delete("/api/projects")' in source
    assert "async def delete_projects_bulk(payload:BulkDeleteRequest)" in source
    assert "await _delete_single_project(job_id)" in source
    assert 'payload.confirm != "Delete"' in source


if __name__ == "__main__":
    unittest.main()
