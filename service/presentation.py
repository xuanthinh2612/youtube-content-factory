import bleach
import markdown as md
from service.languages import language_display_name


def split_output_title(content):
    lines = str(content or "").splitlines()
    first_line_index = next((index for index, line in enumerate(lines) if line.strip()), None)
    if first_line_index is None:
        return "", str(content or "").strip()

    first_line = lines[first_line_index].strip()
    if not first_line.startswith("# "):
        return "", str(content or "").strip()

    title = first_line[2:].strip().strip("# ")
    body = "\n".join(lines[first_line_index + 1:]).lstrip()
    return title, body


def generated_display_title(job, export_data):
    prompt = (job.request.user_promt or "").strip()
    for output in (export_data or {}).get("outputs", {}).values():
        heading, _ = split_output_title(output.get("content", ""))
        if heading:
            return heading
        title = str(output.get("title") or "").strip()
        if title and title != prompt[:96]:
            return title

    title = str((export_data or {}).get("title") or "").strip()
    if title and title != prompt[:96]:
        return title
    return job.name


def normalize_output_data(job, export_data):
    normalized = dict(export_data or {})
    normalized["title"] = generated_display_title(job, normalized)
    normalized_outputs = {}
    for language, output in normalized.get("outputs", {}).items():
        output = dict(output)
        heading, body = split_output_title(output.get("content", ""))
        output["title"] = heading or str(output.get("title") or normalized["title"])
        output["content"] = body
        normalized_outputs[language] = output
    if "outputs" in normalized:
        normalized["outputs"] = normalized_outputs
    return normalized


def build_output_markdown(job, export_data, include_title=True):
    export_data = normalize_output_data(job, export_data)
    outputs = export_data.get("outputs", {})
    title = generated_display_title(job, export_data)
    sections = [f"# {title}".strip()] if include_title else []
    for language, output in outputs.items():
        output_title, body = split_output_title(output.get("content", ""))
        output_title = output_title or str(output.get("title") or "").strip()
        language_heading = f"Ngôn ngữ: {language_display_name(language)}"
        if output_title and output_title != title and len(outputs) > 1:
            language_heading = f"{language_heading} — {output_title}"
        sections.extend((f"## {language_heading}", body))
    user_promt = export_data.get("user_promt", export_data.get("topic"))
    if not outputs and user_promt:
        sections.extend(("## Requested prompt", user_promt))
    if export_data.get("error"):
        sections.extend(("## Generation error", export_data["error"]))
    return "\n\n".join(section for section in sections if section).rstrip() + "\n"


ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS) | {
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "code", "blockquote",
    "ul", "ol", "li", "hr", "br", "table", "thead", "tbody", "tr", "th", "td",
}
ALLOWED_ATTRS = {"a": ["href", "title", "rel"], "code": ["class"], "pre": ["class"]}


def render_markdown_file(path):
    return render_sanitized_markdown(path.read_text(encoding="utf-8"))


def render_sanitized_markdown(text):
    rendered = md.markdown(text or "", extensions=["tables", "fenced_code", "sane_lists", "nl2br"])
    return bleach.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS,
                        protocols={"http", "https", "mailto"}, strip=True)


def format_activity_event(activity_event):
    presented = dict(activity_event)
    node = activity_event.get("node") or activity_event.get("type")
    title = {"director": "Director", "writer": "Writer", "reviewer": "Reviewer",
             "editor": "Editor", "rewriter": "Editor"}.get(node, str(node).title())
    if activity_event.get("language"):
        title = f"{title} · {language_display_name(activity_event['language'])}"
        presented["language_name"] = language_display_name(activity_event["language"])
    presented["display_node"] = title
    presented["message_html"] = render_sanitized_markdown(str(activity_event.get("message") or ""))
    return presented


def build_agent_status_summary(events, stage=None, running=False):
    states = {key: {"status": "idle", "message": ""} for key in ("director", "writer", "reviewer", "editor")}
    if running and stage in states:
        states[stage]["status"] = "running"
    for activity_event in events:
        node = activity_event.get("node")
        if node not in states:
            continue
        state = states[node]
        if activity_event.get("type") == "node_start":
            state["status"] = "running"
        elif activity_event.get("type") == "node_success":
            state["status"] = "success"
        elif activity_event.get("type") == "node_error":
            state["status"] = "failed"
        elif activity_event.get("type") == "step" and activity_event.get("status") in ("running", "success", "failed"):
            state["status"] = activity_event["status"]
        state["message"] = (
            "Output ready" if activity_event.get("type") == "node_success"
            else activity_event.get("message") or state["message"]
        )
    return states
