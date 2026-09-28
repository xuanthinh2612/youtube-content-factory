from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_template(name):
    return (ROOT / "templates" / name).read_text(encoding="utf-8")


def test_flask_html_pages_cover_create_projects_and_outputs():
    assert 'action="{{ url_for(\'create_project\') }}"' in read_template("home.html")
    assert "project-select" in read_template("list.html")
    assert "url_for('outputs_page'" in read_template("detail.html")
    assert "content.json" in read_template("outputs.html")


def test_pages_show_names_progress_and_agent_activity():
    detail = read_template("detail.html")
    listing = read_template("list.html")
    assert "{{ project.name }}" in detail
    assert "{{ project.progress }}" in detail
    assert "('director', 'writer', 'reviewer', 'editor')" in detail
    assert "class=\"agent-workflow\"" in detail
    assert "class=\"agent-connector\"" in detail
    assert "data-agent-state=\"{{ name }}\"" in detail
    assert "data-agent-status" in detail and "data-agent-message" in detail
    assert "{{ project.name }}" in listing


def test_pages_expose_stop_delete_and_bulk_actions():
    detail = read_template("detail.html")
    listing = read_template("list.html")
    assert "cancel_job_from_page" in detail and "delete_job_from_page" in detail
    assert "cancel_job_from_page" in listing
    assert "bulk_delete_projects" in listing and "project_ids" in listing
    assert "data-select-all" in listing and "data-bulk-delete" in listing
    assert 'type="checkbox" name="confirm"' not in listing and 'type="checkbox" name="confirm"' not in detail
    assert 'type="hidden" name="confirm" value="Delete"' in listing
    assert 'type="hidden" name="confirm" value="Delete"' in detail
    assert "data-confirm-delete" in listing and "data-confirm-delete" in detail
