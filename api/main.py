import json
import threading
from io import BytesIO

from flask import Flask, Response, abort, jsonify, redirect, render_template, request, send_file, url_for
from flask_sock import Sock
from pydantic import ValidationError
from simple_websocket import ConnectionClosed

from service.serializers import serialize_details, serialize_status
from service.models import BulkProjectDeleteRequest, ProjectGenerationRequest, ProjectJob
from service.languages import OUTPUT_LANGUAGES, language_display_name
from service.observability.logging_setup import configure_application_logging
from service.errors import ServiceError
from service.operations import (
    cancel_job,
    create_job as create_service,
    delete_and_files as delete_service,
    delete_jobs_bulk as delete_projects_bulk_service,
)
from service.presentation import (
    build_agent_status_summary,
    build_output_markdown,
    format_activity_event,
    generated_display_title,
    render_markdown_file,
    render_sanitized_markdown,
)
from service.storage.database import database
from service.storage.file_store import file_store
from service.background_runtime import get_queue_status, run_async_operation, background_runtime

configure_application_logging()

app = Flask(__name__, template_folder="../templates", static_folder="../static")
sock = Sock(app)


def prepare_job_display(job):
    if not job:
        return {}
    export_data = job.result or file_store.read_json(job.id, "content.json", {}) or {}
    job.name = generated_display_title(job, export_data)
    return export_data


@app.before_request
def start_background_services_before_request():
    background_runtime.start_background_runtime()


@app.errorhandler(ValidationError)
def handle_validation_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"detail": error.errors(include_url=False)}), 422
    return render_template("home.html", form=request.form, error=" ".join(
        str(item.get("msg", "Invalid input")) for item in error.errors()
    ), clone_source=None), 400


@app.errorhandler(404)
def handle_not_found_error(error):
    if request.path.startswith("/api/") or request.path == "/health":
        return jsonify({"detail": "Not found"}), 404
    return render_template("error.html", code=404, message="Project or page not found."), 404


@app.errorhandler(400)
@app.errorhandler(409)
def handle_bad_request_or_conflict(error):
    if request.path.startswith("/api/"):
        return jsonify({"detail": getattr(error, "description", "Request could not be completed")}), error.code
    return render_template("error.html", code=error.code, message=error.description), error.code


@app.errorhandler(ServiceError)
def handle_service_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"detail": error.message}), error.status_code
    return render_template("error.html", code=error.status_code, message=error.message), error.status_code


@app.get("/health")
def health_check():
    return jsonify({"ok": True, "version": "7.9.0", "queue": run_async_operation(get_queue_status())})


# JSON API retained for scripts and integrations.
@app.post("/api/generate")
def create_job_from_api():
    payload = ProjectGenerationRequest.model_validate(request.get_json(force=True))
    job = run_async_operation(create_service(payload))
    return jsonify({"job_id": job.id, "view_url": f"/view/{job.id}", "monitor_url": f"/projects/{job.id}"})


@app.get("/api/projects")
def list_jobs_from_api():
    jobs = run_async_operation(database.list_jobs(limit=request.args.get("limit", 200, type=int), status=request.args.get("status")))
    for job in jobs:
        prepare_job_display(job)
    return jsonify({"items": [serialize_details(job) for job in jobs], "queue": run_async_operation(get_queue_status())})


@app.get("/api/projects/<job_id>")
def get_job_from_api(job_id):
    job = run_async_operation(database.get_job(job_id))
    if not job:
        abort(404, "Project not found")
    prepare_job_display(job)
    return jsonify(serialize_details(job))


@app.post("/api/projects/<job_id>/cancel")
def cancel_job_from_api(job_id):
    return jsonify(run_async_operation(cancel_job(job_id)))


@app.delete("/api/projects/<job_id>")
def delete_job_from_api(job_id):
    if request.args.get("confirm", "") != "Delete":
        abort(400, "Type Delete exactly to confirm project deletion")
    if not run_async_operation(delete_service(job_id)):
        abort(404, "Project not found")
    return jsonify({"ok": True, "deleted_project_id": job_id})


@app.delete("/api/projects")
def bulk_delete_jobs_from_api():
    payload = BulkProjectDeleteRequest.model_validate(request.get_json(force=True))
    return jsonify(run_async_operation(delete_projects_bulk_service(payload)))


@app.get("/api/projects/<job_id>/events")
def list_events_from_api(job_id):
    if not run_async_operation(database.get_job(job_id)):
        abort(404, "Project not found")
    after = request.args.get("after", 0, type=int)
    events = run_async_operation(database.list_events_after(job_id, after, 1000))
    return jsonify({"items": [activity_event for activity_event in events if activity_event.get("type") in ("node_success", "node_error")]})


@app.get("/api/projects/<job_id>/events/stream")
def stream_events_from_api(job_id):
    if not run_async_operation(database.get_job(job_id)):
        abort(404, "Project not found")
    try:
        cursor = max(int(request.headers.get("Last-Event-ID", 0)), int(request.args.get("after", 0)))
    except ValueError:
        cursor = 0

    def stream():
        nonlocal cursor
        while True:
            events = run_async_operation(database.list_events_after(job_id, cursor, 200))
            for activity_event in events:
                cursor = activity_event["id"]
                if activity_event.get("type") in ("node_success", "node_error"):
                    yield f"id: {cursor}\ndata: {json.dumps(activity_event, ensure_ascii=False)}\n\n"
            job = run_async_operation(database.get_job(job_id))
            if not events and (not job or job.status.value in ("completed", "failed", "cancelled")):
                break
            if not events:
                yield ": keepalive\n\n"
            threading.Event().wait(.75)

    return Response(stream(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@sock.route("/ws/projects/<job_id>")
def stream_status_updates(ws, job_id):
    if not run_async_operation(database.get_job(job_id)):
        ws.close(reason=1008, message="Project not found")
        return

    cursor = 0
    previous = None
    first = True
    try:
        while True:
            job = run_async_operation(database.get_job(job_id))
            if not job:
                ws.close(reason=1008, message="Project not found")
                return
            prepare_job_display(job)
            events = run_async_operation(database.list_events_after(job_id, cursor, 200))
            if events:
                cursor = events[-1]["id"]
            signature = (job.name, job.status.value, job.stage, job.progress, job.error)
            if first or events or signature != previous:
                ws.send(json.dumps({
                    "type": "project_update",
                    "project": serialize_details(job),
                    "events": [
                        format_activity_event(activity_event) for activity_event in events
                        if activity_event.get("type") in ("node_success", "node_error")
                    ],
                }, ensure_ascii=False))
                first = False
                previous = signature
            if job.status.value in ("completed", "failed", "cancelled"):
                break

            try:
                incoming = ws.receive(timeout=0.75)
            except TimeoutError:
                incoming = None
            if incoming:
                try:
                    message = json.loads(incoming)
                except (TypeError, json.JSONDecodeError):
                    message = {}
                if isinstance(message, dict) and message.get("type") == "ping":
                    ws.send('{"type":"pong"}')
    except (ConnectionClosed, ConnectionError, OSError):
        return


@sock.route("/ws/projects")
def stream_list_updates(ws):
    previous = None
    try:
        while True:
            jobs = run_async_operation(database.list_jobs(limit=200))
            for job in jobs:
                prepare_job_display(job)
            projects = [serialize_status(job) for job in jobs]
            signature = tuple(
                (job.id, job.name, job.status.value, job.stage, job.progress, job.error)
                for job in jobs
            )
            if signature != previous:
                ws.send(json.dumps({"type": "projects_update", "projects": projects}, ensure_ascii=False))
                previous = signature
            try:
                incoming = ws.receive(timeout=0.75)
            except TimeoutError:
                incoming = None
            if incoming:
                try:
                    message = json.loads(incoming)
                except (TypeError, json.JSONDecodeError):
                    message = {}
                if isinstance(message, dict) and message.get("type") == "ping":
                    ws.send('{"type":"pong"}')
    except (ConnectionClosed, ConnectionError, OSError):
        return


@app.get("/api/projects/<job_id>/files")
def list_files_from_api(job_id):
    if not run_async_operation(database.get_job(job_id)):
        abort(404, "Project not found")
    names = ["content.md"] if file_store.resolve_read_path(job_id, "content.md") is not None else []
    return jsonify({"files": names})


@app.get("/api/system/queue")
def get_background_queue_status_from_api():
    return jsonify(run_async_operation(get_queue_status()))


@app.get("/api/jobs/<job_id>/download/<path:file_path>")
def download_file_from_api(job_id, file_path):
    job = run_async_operation(database.get_job(job_id))
    if not job:
        abort(404, "Project not found")
    export_data = prepare_job_display(job)
    if file_path == "content.md" and export_data.get("outputs"):
        generated_markdown = build_output_markdown(job, export_data).encode("utf-8")
        return send_file(BytesIO(generated_markdown), as_attachment=True, download_name="content.md", mimetype="text/markdown")
    if file_path != "content.md":
        abort(404, "File not found")
    path = file_store.resolve_read_path(job_id, file_path)
    if path is None:
        abort(404, "File not found")
    return send_file(path, as_attachment=True, download_name=path.name)


@app.get("/")
def home_page():
    form = {"user_promt": "", "niche": "story", "provider": "openai", "languages": ["vi"], "duration_minutes": 10}
    clone_source = None
    clone_id = request.args.get("clone", "")
    if clone_id:
        source = run_async_operation(database.get_job(clone_id))
        if source:
            form = source.request.model_dump(by_alias=True)
            clone_source = source
        else:
            return render_template("home.html", form=form, clone_source=None, error="Source project was not found.",
                                   output_languages=OUTPUT_LANGUAGES), 404
    output_languages = list(OUTPUT_LANGUAGES)
    known_language_codes = {code for code, _ in output_languages}
    for language in form.get("languages", []):
        if language not in known_language_codes:
            output_languages.append((language, language_display_name(language)))
            known_language_codes.add(language)
    return render_template("home.html", form=form, clone_source=clone_source, error=None,
                           output_languages=output_languages)


@app.post("/projects")
def create_job():
    form = request.form
    niche = form.get("niche", "story")
    languages = form.getlist("languages")
    payload = ProjectGenerationRequest.model_validate({
        "user_promt": form.get("user_promt", "").strip(), "niche": niche,
        "provider": "openai", "sub_niche": form.get("sub_niche", "").strip(),
        "languages": languages,
        "duration_minutes": form.get("duration_minutes", 10),
        "style": form.get("style", "").strip(), "tone": form.get("tone", "").strip(),
        "audience": form.get("audience", "").strip(), "extra_instructions": form.get("extra_instructions", "").strip(),
    })
    job = run_async_operation(create_service(payload))
    return redirect(url_for("detail_page", job_id=job.id), code=303)


@app.get("/projects")
def list_page():
    jobs = run_async_operation(database.list_jobs(limit=200))
    for job in jobs:
        prepare_job_display(job)
    output_languages_by_project = {
        job.id: [language_display_name(code) for code in job.request.languages]
        for job in jobs
    }
    return render_template("list.html", projects=jobs, output_languages_by_project=output_languages_by_project,
                           queue=run_async_operation(get_queue_status()))


@app.post("/projects/bulk-delete")
def bulk_delete_jobs_from_form():
    ids = request.form.getlist("project_ids")
    confirm = request.form.get("confirm")
    payload = BulkProjectDeleteRequest.model_validate({"project_ids": ids, "confirm": confirm})
    run_async_operation(delete_projects_bulk_service(payload))
    return redirect(url_for("list_page"), code=303)


@app.post("/projects/<job_id>/cancel")
def cancel_job_from_page(job_id):
    run_async_operation(cancel_job(job_id))
    return redirect(url_for("detail_page", job_id=job_id), code=303)


@app.post("/projects/<job_id>/delete")
def delete_job_from_page(job_id):
    if request.form.get("confirm") != "Delete":
        abort(400, "Select the confirmation box to delete this project.")
    if not run_async_operation(delete_service(job_id)):
        abort(404, "Project not found")
    return redirect(url_for("list_page"), code=303)


@app.get("/projects/<job_id>")
def detail_page(job_id):
    job = run_async_operation(database.get_job(job_id))
    if not job:
        abort(404, "Project not found")
    prepare_job_display(job)
    events = run_async_operation(database.list_events_after(job_id, 0, 200))
    events = [
        format_activity_event(activity_event) for activity_event in events
        if activity_event.get("type") in ("node_success", "node_error")
    ]
    return render_template("detail.html", project=job, events=events,
                           output_languages=[language_display_name(code) for code in job.request.languages],
                           agents=build_agent_status_summary(events, job.stage, job.status.value == "running"),
                           terminal=job.status.value in ("completed", "failed", "cancelled"))


@app.get("/view/<job_id>")
def content_page(job_id):
    job = run_async_operation(database.get_job(job_id))
    if not job:
        abort(404, "Job not found")
    export_data = prepare_job_display(job)
    if export_data.get("outputs"):
        body = render_sanitized_markdown(
            build_output_markdown(job, export_data, include_title=False)
        )
    else:
        markdown_path = file_store.resolve_read_path(job_id, "content.md")
        if markdown_path is None:
            body = "<p>Content is not ready yet.</p>"
        else:
            body = render_markdown_file(markdown_path)
    return render_template("content_view.html", project=job, content=body)
