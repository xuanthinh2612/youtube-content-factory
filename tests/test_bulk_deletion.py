import tempfile
import unittest
from pathlib import Path

import pytest

from service.settings import app_settings
from service.models import BulkProjectDeleteRequest, ProjectGenerationRequest, ProjectJob, ProjectStatus
from service.storage.database import database
from service.storage.file_store import file_store
from service.storage.job_store import job_store
from service.errors import ServiceError
from service.operations import delete_jobs_bulk


ROOT = Path(__file__).resolve().parents[1]


class BulkDeleteProjectsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_db_path = app_settings.db_path
        self.old_data_dir = app_settings.data_dir
        self.old_base = file_store.projects_root_directory
        app_settings.db_path = str(Path(self.temp_dir.name) / "factory.db")
        app_settings.data_dir = self.temp_dir.name
        await database.initialize_database()
        # `file_store` is a process-wide singleton created at import time, so
        # tests must repoint its resolved base dir to the temp dir directly.
        file_store.projects_root_directory = Path(self.temp_dir.name).resolve()

    async def asyncTearDown(self):
        app_settings.db_path = self.old_db_path
        app_settings.data_dir = self.old_data_dir
        file_store.projects_root_directory = self.old_base
        self.temp_dir.cleanup()

    @staticmethod
    def job(job_id: str, status: ProjectStatus = ProjectStatus.completed) -> ProjectJob:
        return ProjectJob(
            id=job_id,
            request=ProjectGenerationRequest(user_promt="A bulk delete test topic", niche="story"),
            status=status,
            stage=status.value,
            progress=100,
        )

    async def test_delete_projects_bulk_only_removes_selected_projects(self):
        keep = self.job("keep-project")
        remove_a = self.job("remove-a")
        remove_b = self.job("remove-b")
        for job in (keep, remove_a, remove_b):
            await job_store.save_job(job)
            folder = file_store.ensure_folder(job.id)
            (folder / "artifact.txt").write_text("generated", encoding="utf-8")

        payload = BulkProjectDeleteRequest(ids=[remove_a.id, remove_b.id], confirm="Delete")
        result = await delete_jobs_bulk(payload)

        self.assertEqual(sorted(result["deleted_project_ids"]), [remove_a.id, remove_b.id])
        self.assertEqual(result["missing_project_ids"], [])

        self.assertIsNone(await job_store.get_job(remove_a.id))
        self.assertIsNone(await job_store.get_job(remove_b.id))
        self.assertFalse(file_store.directory(remove_a.id).exists())
        self.assertFalse(file_store.directory(remove_b.id).exists())

        untouched = await job_store.get_job(keep.id)
        self.assertIsNotNone(untouched)
        self.assertTrue(file_store.directory(keep.id).exists())

    async def test_delete_projects_bulk_reports_missing_ids_without_failing(self):
        existing = self.job("existing-project")
        await job_store.save_job(existing)

        payload = BulkProjectDeleteRequest(ids=[existing.id, "never-created"], confirm="Delete")
        result = await delete_jobs_bulk(payload)

        self.assertEqual(result["deleted_project_ids"], [existing.id])
        self.assertEqual(result["missing_project_ids"], ["never-created"])

    async def test_delete_projects_bulk_rejects_wrong_confirmation(self):
        existing = self.job("existing-project")
        await job_store.save_job(existing)

        payload = BulkProjectDeleteRequest(ids=[existing.id], confirm="delete")
        with self.assertRaises(ServiceError) as ctx:
            await delete_jobs_bulk(payload)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIsNotNone(await job_store.get_job(existing.id))


def test_bulk_delete_request_rejects_invalid_ids():
    with pytest.raises(Exception):
        BulkProjectDeleteRequest(ids=["../etc"], confirm="Delete")
    with pytest.raises(Exception):
        BulkProjectDeleteRequest(ids=[], confirm="Delete")


def test_bulk_delete_endpoint_reuses_single_delete_semantics():
    source = (ROOT / "api/main.py").read_text(encoding="utf-8")
    service = (ROOT / "service/operations.py").read_text(encoding="utf-8")
    assert '@app.delete("/api/projects")' in source
    assert "def api_delete_projects_bulk()" in source
    assert "await delete_project(job_id)" in service
    assert 'payload.confirm != "Delete"' in service


if __name__ == "__main__":
    unittest.main()
