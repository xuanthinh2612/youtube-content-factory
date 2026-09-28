from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from zoneinfo import ZoneInfo
import re
from pydantic import BaseModel, Field, model_validator


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class JobStatus(str, Enum):
    queued="queued"
    running="running"
    completed="completed"
    failed="failed"
    cancelled="cancelled"


_LANG_RE=re.compile(r"^[a-z]{2,3}(?:-[a-z0-9]{2,8}){0,2}$")
_PROJECT_ID_RE=re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class GenerateRequest(BaseModel):
    topic: str = Field(min_length=3,max_length=20000)
    niche: Literal["fact","story","news","music","song","visual"]
    sub_niche: str = Field(default="",max_length=300)
    languages: list[str] = Field(default_factory=lambda:["vi"],min_length=1,max_length=12)
    duration_minutes: int = Field(default=10, ge=1, le=60)
    style: str = Field(default="",max_length=500)
    tone: str = Field(default="",max_length=500)
    audience: str = Field(default="",max_length=500)
    extra_instructions: str = Field(default="",max_length=12000)
    timezone: str = Field(default="",max_length=80)
    aspect_ratio: Literal["","16:9","9:16","1:1","4:3","21:9"] = ""
    music_provider: str = Field(default="generic",min_length=1,max_length=80)

    # Optional downstream linkage: Visual projects can consume an existing content
    # project's canonical blueprint + final narration instead of re-inventing context.
    source_project_id: str = Field(default="",max_length=128)

    @model_validator(mode="after")
    def normalize(self):
        # Public/API-friendly alias; the internal workflow key remains `music`
        # for compatibility with persisted projects and graph definitions.
        if self.niche=="song":
            self.niche="music"
        if self.niche=="music" and "duration_minutes" not in self.model_fields_set:
            self.duration_minutes=4
        if self.niche=="music" and self.duration_minutes>8:
            raise ValueError("Song length must be between 1 and 8 minutes for one Suno generation")
        langs=[(x or "").strip().lower() for x in self.languages if (x or "").strip()]
        langs=list(dict.fromkeys(langs)) or ["vi"]
        bad=[x for x in langs if not _LANG_RE.fullmatch(x)]
        if bad:
            raise ValueError(f"Invalid language code(s): {', '.join(bad[:4])}")
        self.languages=langs

        tz=(self.timezone or "").strip()
        if tz:
            try:
                ZoneInfo(tz)
            except Exception as exc:
                raise ValueError(f"Invalid timezone: {tz}") from exc
            self.timezone=tz

        source_id=(self.source_project_id or "").strip()
        if source_id and not _PROJECT_ID_RE.fullmatch(source_id):
            raise ValueError("Invalid source_project_id")
        self.source_project_id=source_id
        return self


class Job(BaseModel):
    id: str
    name: str = "Preparing project…"
    request: GenerateRequest
    status: JobStatus = JobStatus.queued
    stage: str = "queued"
    progress: int = 0
    trend_score: float | None = None
    error: str | None = None
    created_at: str = Field(default_factory=utcnow)
    updated_at: str = Field(default_factory=utcnow)
    started_at: str | None = None
    completed_at: str | None = None
    result: dict | None = None


class BulkDeleteRequest(BaseModel):
    project_ids: list[str] = Field(min_length=1, max_length=200)
    confirm: str = Field(default="", max_length=20)

    @model_validator(mode="after")
    def normalize(self):
        ids=[]
        for value in self.project_ids:
            item=(value or "").strip()
            if not item or not _PROJECT_ID_RE.fullmatch(item):
                raise ValueError(f"Invalid project id: {item[:120]}")
            ids.append(item)
        self.project_ids=list(dict.fromkeys(ids))
        if not self.project_ids:
            raise ValueError("project_ids must contain at least one valid id")
        return self
