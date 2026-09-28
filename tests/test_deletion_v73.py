from pathlib import Path

from service.settings import app_settings
from service.storage.file_store import ProjectFileStore


ROOT=Path(__file__).resolve().parents[1]


def test_file_store_delete_removes_tree(tmp_path):
    old=app_settings.data_dir
    app_settings.data_dir=str(tmp_path)
    try:
        store=ProjectFileStore()
        folder=store.ensure_folder("project-123")
        (folder/"nested").mkdir()
        (folder/"nested"/"artifact.txt").write_text("generated",encoding="utf-8")
        assert folder.exists()
        store.delete_folder("project-123")
        assert not folder.exists()
    finally:
        app_settings.data_dir=old


def test_delete_endpoint_requires_exact_delete_confirmation():
    source=(ROOT/"api/main.py").read_text(encoding="utf-8")
    service=(ROOT/"service/operations.py").read_text(encoding="utf-8")
    assert '@app.delete("/api/projects/<job_id>")' in source
    assert 'confirm != "Delete"' in source or 'payload.confirm != "Delete"' in service
    assert 'await background_queue.cancel_job(id)' in service
    assert 'file_store.delete_folder(id)' in service
    assert 'return await job_store.delete_job(id)' in service


def test_database_delete_removes_events_before_project():
    source=(ROOT/"service/storage/database.py").read_text(encoding="utf-8")
    assert 'DELETE FROM events WHERE project_id=?' in source
    assert 'DELETE FROM projects WHERE id=?' in source
