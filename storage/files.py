import json
import re
import shutil
from pathlib import Path
from core.config import settings

_SAFE_COMPONENT=re.compile(r"^[A-Za-z0-9._-]{1,180}$")


class FileStore:
    def __init__(self):
        self.base=settings.output_dir().resolve()

    def _job_component(self,job_id):
        value=str(job_id or "").strip()
        if not _SAFE_COMPONENT.fullmatch(value) or value in {".",".."}:
            raise ValueError("invalid project id")
        return value

    def path(self,job_id):
        return self.base/self._job_component(job_id)

    def folder(self,job_id):
        p=self.path(job_id)
        p.mkdir(parents=True,exist_ok=True)
        return p

    def existing_folder(self,job_id):
        p=self.path(job_id)
        return p if p.exists() and p.is_dir() else None

    def resolve_read(self,job_id,rel):
        root=self.path(job_id).resolve()
        candidate=(root/str(rel or "")).resolve()
        if candidate != root and root not in candidate.parents:
            return None
        return candidate if candidate.exists() and candidate.is_file() else None

    def resolve_write(self,job_id,rel):
        root=self.folder(job_id).resolve()
        candidate=(root/str(rel or "")).resolve()
        if candidate == root or root not in candidate.parents:
            raise ValueError("invalid project-relative path")
        return candidate

    def atomic_text(self,path,text):
        path.parent.mkdir(parents=True,exist_ok=True)
        tmp=path.with_suffix(path.suffix+".tmp")
        tmp.write_text(text,encoding="utf-8")
        tmp.replace(path)

    def write_json(self,job_id,rel,obj):
        p=self.resolve_write(job_id,rel)
        self.atomic_text(p,json.dumps(obj,ensure_ascii=False,indent=2))
        return p

    def write_text(self,job_id,rel,text):
        p=self.resolve_write(job_id,rel)
        self.atomic_text(p,text)
        return p

    def read_json(self,job_id,rel,default=None):
        p=self.resolve_read(job_id,rel)
        if p is None:
            return default
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return default

    def read_text(self,job_id,rel,default=""):
        p=self.resolve_read(job_id,rel)
        if p is None:
            return default
        try:
            return p.read_text(encoding="utf-8")
        except Exception:
            return default

    def delete_project(self,job_id):
        p=self.path(job_id)
        if p.exists() and p.is_dir():
            shutil.rmtree(p)
        return not p.exists()


file_store=FileStore()
