import json
import re
import unicodedata
from pathlib import Path

from service.openai_client import send_openai_response
from service.schemas.story_audio import STORY_AUDIO_OUTPUT_FORMAT
from service.settings import app_settings


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
PROMPT_FILES = {
    "image": ("videoJsonCommonGuild.md", "jsonForImageGuild.md"),
    "video": ("videoJsonCommonGuild.md", "jsonForVideoGuild.md"),
}


def story_project_json_directory(project_type: str) -> Path:
    if project_type not in PROMPT_FILES:
        raise ValueError("Loại project JSON không hợp lệ.")
    directory = PROJECT_ROOT / "data" / "project_json" / project_type
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _filename_stem(title: str) -> str:
    normalized = unicodedata.normalize("NFKC", title)
    stem = re.sub(r"[^\w-]+", "-", normalized, flags=re.UNICODE).strip("-_")
    return (stem or "flow-hub-project")[:80]


def _validate_project_json(value):
    if not isinstance(value, dict):
        raise ValueError("OpenAI trả về JSON không phải object.")
    if value.get("format") != "flow-hub-canvas-project":
        raise ValueError("JSON không có format Flow Hub Canvas hợp lệ.")
    if value.get("format_version") != 1:
        raise ValueError("format_version phải là 1.")
    if not isinstance(value.get("auto_gen"), bool):
        raise ValueError("auto_gen phải là giá trị boolean.")
    if not isinstance(value.get("project"), dict):
        raise ValueError("project phải là JSON object.")
    if not isinstance(value.get("nodes"), list) or not isinstance(value.get("edges"), list):
        raise ValueError("nodes và edges phải là JSON list.")
    node_ids = set()
    for index, node in enumerate(value["nodes"], start=1):
        if not isinstance(node, dict):
            raise ValueError(f"Node {index} phải là JSON object.")
        required = {"id", "title", "type", "prompt", "generation", "status"}
        if required - set(node):
            raise ValueError(f"Node {index} thiếu trường bắt buộc: {', '.join(sorted(required - set(node)))}.")
        node_id = node["id"]
        if not isinstance(node_id, str) or not node_id or node_id in node_ids:
            raise ValueError("Mỗi node phải có id dạng chuỗi duy nhất.")
        node_ids.add(node_id)
        if not isinstance(node["generation"], dict):
            raise ValueError(f"generation của node {node_id} phải là JSON object.")
    for index, edge in enumerate(value["edges"], start=1):
        if not isinstance(edge, dict) or edge.get("relation") != "canvas":
            raise ValueError(f"Edge {index} phải là JSON object có relation canvas.")
        if edge.get("source") not in node_ids or edge.get("target") not in node_ids:
            raise ValueError(f"Edge {index} có source/target không tồn tại trong nodes.")


def _save_without_overwrite(project_type: str, title: str, document: dict) -> str:
    stem = _filename_stem(title)
    directory = story_project_json_directory(project_type)
    suffix = 1
    while True:
        filename = f"{stem}.json" if suffix == 1 else f"{stem}-{suffix}.json"
        destination = directory / filename
        try:
            with destination.open("x", encoding="utf-8", newline="\n") as output:
                json.dump(document, output, ensure_ascii=False, indent=2)
                output.write("\n")
            return filename
        except FileExistsError:
            suffix += 1


async def create_story_project_json(project_type: str, content: str) -> dict:
    if project_type not in PROMPT_FILES:
        raise ValueError("Loại project JSON không hợp lệ.")
    if not app_settings.openai_api_key:
        raise RuntimeError("Chưa cấu hình OPENAI_API_KEY trong .env.")

    try:
        instructions = "\n\n".join(
            (PROMPTS_DIR / filename).read_text(encoding="utf-8")
            for filename in PROMPT_FILES[project_type]
        )
    except OSError as error:
        raise RuntimeError(f"Không đọc được file prompt Flow Hub: {error}") from error

    response = await send_openai_response(
        None,
        instructions,
        "Hãy chuyển nguyên nội dung đầu vào thành duy nhất một project JSON Flow Hub Canvas hợp lệ theo hướng dẫn.\n\n"
        "NỘI DUNG ĐẦU VÀO (giữ nguyên nội dung, không bỏ sót):\n"
        f"{content}",
        output_format=STORY_AUDIO_OUTPUT_FORMAT,
    )
    try:
        document = json.loads(response.output_text)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError("OpenAI trả về nội dung không phải JSON hợp lệ.") from error
    _validate_project_json(document)
    title = str(document["project"].get("name") or "flow-hub-project").strip()
    filename = _save_without_overwrite(project_type, title, document)
    return {
        "project_name": title,
        "filename": filename,
        "path": f"data/project_json/{project_type}/{filename}",
        "download_url": f"/data/project-json/{project_type}/{filename}",
    }
