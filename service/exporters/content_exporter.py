from pathlib import Path
from service.languages import language_display_name


def write_content_files(folder: Path, title: str, export_data: dict) -> dict[str, str]:
    """Write the final Markdown file for a project."""
    folder.mkdir(parents=True, exist_ok=True)
    markdown_sections = [f"# {title}".strip()]
    for output_language, generated_output in export_data.get("outputs", {}).items():
        markdown_sections.extend((f"## Ngôn ngữ: {language_display_name(output_language)}", generated_output.get("content", "")))
    user_promt = export_data.get("user_promt", export_data.get("topic"))
    if not export_data.get("outputs") and user_promt:
        markdown_sections.extend(("## Requested prompt", user_promt))
    if export_data.get("error"):
        markdown_sections.extend(("## Generation error", export_data["error"]))

    markdown_path = folder / "content.md"
    markdown_path.write_text("\n\n".join(markdown_sections).rstrip() + "\n", encoding="utf-8")
    return {"md": str(markdown_path)}
