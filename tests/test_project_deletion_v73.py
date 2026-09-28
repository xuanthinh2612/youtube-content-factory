from pathlib import Path

from core.config import settings
from storage.files import FileStore


ROOT=Path(__file__).resolve().parents[1]


def test_project_file_store_delete_removes_project_tree(tmp_path):
    old=settings.data_dir
    settings.data_dir=str(tmp_path)
    try:
        store=FileStore()
        folder=store.folder("project-123")
        (folder/"nested").mkdir()
        (folder/"nested"/"artifact.txt").write_text("generated",encoding="utf-8")
        assert folder.exists()
        store.delete_project("project-123")
        assert not folder.exists()
    finally:
        settings.data_dir=old


def test_delete_endpoint_requires_exact_delete_confirmation():
    source=(ROOT/"api/main.py").read_text(encoding="utf-8")
    assert '@app.delete("/api/projects/{job_id}")' in source
    assert 'confirm != "Delete"' in source
    assert 'await project_queue.cancel(job_id)' in source
    assert 'file_store.delete_project(job_id)' in source
    assert 'await job_store.delete(job_id)' in source


def test_database_delete_removes_events_before_project():
    source=(ROOT/"storage/database.py").read_text(encoding="utf-8")
    assert 'DELETE FROM events WHERE project_id=?' in source
    assert 'DELETE FROM projects WHERE id=?' in source
