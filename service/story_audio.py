import json
import re
import unicodedata
from pathlib import Path

from service.openai_client import send_openai_response
from service.schemas.story_audio import STORY_AUDIO_OUTPUT_FORMAT
from service.settings import app_settings


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "story_audio_json.md"


def story_audio_directory() -> Path:
    directory = PROJECT_ROOT / "data" / "audio"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _filename_stem(title: str) -> str:
    normalized = unicodedata.normalize("NFKC", title)
    stem = re.sub(r"[^\w-]+", "-", normalized, flags=re.UNICODE).strip("-_")
    return (stem or "story")[:80]


def _validate_story_audio_json(value):
    if not isinstance(value, dict):
        raise ValueError("OpenAI trả về JSON không phải object.")
    if set(value) != {"language", "story_name", "voices", "segments"}:
        raise ValueError("JSON trả về có trường root không đúng schema.")
    if not isinstance(value["language"], str) or not value["language"].strip():
        raise ValueError("language phải là chuỗi và không được để trống.")
    if not isinstance(value["story_name"], str) or not value["story_name"].strip():
        raise ValueError("story_name phải là chuỗi và không được để trống.")
    if not isinstance(value["voices"], dict) or not value["voices"] or not isinstance(value["segments"], list) or not value["segments"]:
        raise ValueError("voices và segments phải là object/list không rỗng.")
    for speaker_id, voice in value["voices"].items():
        if not isinstance(speaker_id, str) or not speaker_id.strip() or not isinstance(voice, dict) or set(voice) != {"name", "elevenlabs_voice_id"}:
            raise ValueError("Mỗi voice phải có đúng name và elevenlabs_voice_id.")
        if not all(isinstance(voice[key], str) for key in voice):
            raise ValueError("Các trường voice phải là chuỗi.")
    for index, segment in enumerate(value["segments"], start=1):
        if not isinstance(segment, dict):
            raise ValueError(f"Segment {index} phải là JSON object có id, speaker_id và text.")
        expected_keys = {"id", "speaker_id", "text"}
        missing = expected_keys - set(segment)
        extra = set(segment) - expected_keys
        if missing or extra:
            problems = []
            if missing:
                problems.append(f"thiếu: {', '.join(sorted(missing))}")
            if extra:
                problems.append(f"thừa: {', '.join(sorted(extra))}")
            raise ValueError(f"Segment {index} phải có đúng id, speaker_id và text ({'; '.join(problems)}).")
        if not all(isinstance(segment[key], str) for key in expected_keys):
            raise ValueError(f"Các trường của segment {index} phải là chuỗi.")
        if segment["speaker_id"] not in value["voices"]:
            raise ValueError("speaker_id trong segment không tồn tại trong voices.")
        if segment["id"] != f"seg_{index:04d}":
            raise ValueError("ID segment phải bắt đầu từ seg_0001 và tiếp tục liên tục.")


def _save_without_overwrite(title: str, document: dict) -> str:
    stem = _filename_stem(title)
    directory = story_audio_directory()
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


async def create_story_audio_json(story: str) -> dict:
    if not app_settings.openai_api_key:
        raise RuntimeError("Chưa cấu hình OPENAI_API_KEY trong .env.")

    instructions = PROMPT_PATH.read_text(encoding="utf-8")
    response = await send_openai_response(
        None,
        instructions,
        (
            "Hãy trả về duy nhất một JSON object theo định dạng Story Audio JSON trong hướng dẫn.\n\n"
            "NỘI DUNG TRUYỆN:\n"
            f"{story}"
        ),
        output_format=STORY_AUDIO_OUTPUT_FORMAT,
    )
    try:
        document = json.loads(response.output_text)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError("OpenAI trả về nội dung không phải JSON hợp lệ.") from error
    _validate_story_audio_json(document)
    story_name = document["story_name"].strip()
    document = {
        "language": document["language"],
        "story_name": story_name,
        "voices": document["voices"],
        "segments": document["segments"],
    }
    filename = _save_without_overwrite(story_name, document)
    return {
        "story_name": story_name,
        "filename": filename,
        "path": f"data/audio/{filename}",
        "download_url": f"/data/audio/{filename}",
    }
