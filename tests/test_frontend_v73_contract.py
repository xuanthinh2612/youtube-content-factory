from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FRONT=ROOT/"frontend/src"


def read(rel):
    return (FRONT/rel).read_text(encoding="utf-8")


def test_duration_is_neutral_from_one_to_sixty_minutes():
    text=read("components/DurationSlider.vue")
    assert 'min="1"' in text and 'max="60"' in text
    assert "recommended" not in text.lower()
    assert "5–30" not in text and "5-30" not in text


def test_project_views_use_generated_name_not_full_prompt():
    for rel in ("views/ProjectView.vue","views/ProjectsView.vue","views/OutputsView.vue"):
        text=read(rel)
        assert ".name" in text, rel
    detail=read("views/ProjectView.vue")
    assert "<h1>{{project.name}}</h1>" in detail
    assert "<h1>{{project.request.topic}}</h1>" not in detail


def test_workflow_has_zoom_fit_and_horizontal_layout():
    graph=read("components/WorkflowGraph.vue")
    project=read("views/ProjectView.vue")
    css=read("styles.css")
    assert "function zoomIn" in graph and "function zoomOut" in graph
    assert "function fitWidth" in graph and "resetZoom" in graph
    assert "LEVEL_GAP" in graph and "graph-scroller" in graph
    assert "monitor-stack" in project
    assert "project-monitor-page" in css and "1600px" in css


def test_delete_uses_plain_confirm_popup_not_typed_text():
    projects=read("views/ProjectsView.vue")
    detail=read("views/ProjectView.vue")
    for text,label in ((projects,"ProjectsView"),(detail,"ProjectView")):
        assert "window.confirm(" in text, label
        assert "'Delete'" in text, label
    assert "confirmation!=='Delete'" not in projects
    assert "Type <code>Delete</code> to confirm" not in projects


def test_projects_view_supports_bulk_selection_and_delete():
    text=read("views/ProjectsView.vue")
    assert "selectedIds" in text
    assert "toggleSelectAll" in text
    assert "deleteSelected" in text
    assert "deleteProjectsBulk" in text
    assert "select-cell" in text


def test_clone_prefills_create_form_from_original_request():
    home=read("views/HomeView.vue")
    detail=read("views/ProjectView.vue")
    projects=read("views/ProjectsView.vue")
    expected_fields=(
        "topic","niche","sub_niche","languages","duration_minutes","style",
        "tone","audience","extra_instructions","timezone","source_project_id",
        "aspect_ratio","music_provider",
    )
    assert "watch(()=>route.query.clone,loadClone,{immediate:true})" in home
    assert "fillFromRequest(project.request)" in home
    for field in expected_fields:
        assert f"request.{field}" in home, field
    assert "Existing outputs are not copied" in home
    assert "query:{clone:id}" in detail
    assert "query:{clone:p.id}" in projects
