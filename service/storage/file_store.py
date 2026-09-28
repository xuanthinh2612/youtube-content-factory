"""Safely read and write files inside each generated project directory."""

import json
import re
import shutil
from pathlib import Path

from service.settings import app_settings


SAFE_PROJECT_FOLDER_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,180}$")


class ProjectFileStore:
    def __init__(self):
        self.projects_root_directory = app_settings.generated_output_directory().resolve()

    def _validate_folder_name(self, id):
        folder_name = str(id or "").strip()
        if not SAFE_PROJECT_FOLDER_PATTERN.fullmatch(folder_name) or folder_name in {".", ".."}:
            raise ValueError("Invalid project ID")
        return folder_name

    def directory(self, id):
        return self.projects_root_directory / self._validate_folder_name(id)

    def ensure_folder(self, id):
        folder = self.directory(id)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def get_existing_folder(self, id):
        folder = self.directory(id)
        return folder if folder.exists() and folder.is_dir() else None

    def resolve_read_path(self, id, relative_path):
        root = self.directory(id).resolve()
        candidate_path = (root / str(relative_path or "")).resolve()
        if candidate_path != root and root not in candidate_path.parents:
            return None
        return candidate_path if candidate_path.exists() and candidate_path.is_file() else None

    def resolve_write_path(self, id, relative_path):
        root = self.ensure_folder(id).resolve()
        candidate_path = (root / str(relative_path or "")).resolve()
        if candidate_path == root or root not in candidate_path.parents:
            raise ValueError("Invalid project-relative path")
        return candidate_path

    def write_text_atomically(self, target_path, text_content):
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = target_path.with_suffix(target_path.suffix + ".tmp")
        temporary_path.write_text(text_content, encoding="utf-8")
        temporary_path.replace(target_path)

    def write_json(self, id, relative_path, json_value):
        target_path = self.resolve_write_path(id, relative_path)
        serialized_json = json.dumps(json_value, ensure_ascii=False, indent=2)
        self.write_text_atomically(target_path, serialized_json)
        return target_path

    def write_text(self, id, relative_path, text_content):
        target_path = self.resolve_write_path(id, relative_path)
        self.write_text_atomically(target_path, text_content)
        return target_path

    def read_json(self, id, relative_path, default=None):
        source_path = self.resolve_read_path(id, relative_path)
        if source_path is None:
            return default
        try:
            return json.loads(source_path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def read_text(self, id, relative_path, default=""):
        source_path = self.resolve_read_path(id, relative_path)
        if source_path is None:
            return default
        try:
            return source_path.read_text(encoding="utf-8")
        except Exception:
            return default

    def delete_folder(self, id):
        folder = self.directory(id)
        if folder.exists() and folder.is_dir():
            shutil.rmtree(folder)
        return not folder.exists()


file_store = ProjectFileStore()
