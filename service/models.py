from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from service.countries import COUNTRY_OUTPUT_LANGUAGE_BY_CODE, VALID_COUNTRY_CODES


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


class ProjectStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


LANGUAGE_CODE_PATTERN = re.compile(r"^[a-z]{2,3}(?:-[a-z0-9]{2,8}){0,2}$")
PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class ProjectGenerationRequest(BaseModel):
    user_promt: str = Field(min_length=3, max_length=20000)
    niche: Literal["fact", "story", "news", "music", "video"]
    provider: Literal["openai"] = "openai"
    sub_niche: str = Field(default="", max_length=300)
    languages: list[str] = Field(default_factory=list)
    duration_minutes: int = Field(default=10, ge=1, le=60)
    style: str = Field(default="", max_length=500)
    tone: str = Field(default="", max_length=500)
    audience: str = Field(default="", max_length=500)
    extra_instructions: str = Field(default="", max_length=12000)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_request_fields(cls, values):
        if isinstance(values, dict):
            values = dict(values)
            if "user_promt" not in values and "topic" in values:
                values["user_promt"] = values.pop("topic")
            legacy_countries = values.pop("output_countries", values.pop("target_countries", []))
            languages = list(values.get("languages") or [])
            for country_code in legacy_countries:
                code = str(country_code or "").strip().upper()
                if code in VALID_COUNTRY_CODES:
                    language = COUNTRY_OUTPUT_LANGUAGE_BY_CODE.get(code, "en")
                    if language not in languages:
                        languages.append(language)
            if languages:
                values["languages"] = languages
        return values

    @model_validator(mode="after")
    def normalize(self):
        languages = [(item or "").strip().lower() for item in self.languages if (item or "").strip()]
        self.languages = list(dict.fromkeys(languages)) or ["vi"]
        invalid = [item for item in self.languages if not LANGUAGE_CODE_PATTERN.fullmatch(item)]
        if invalid:
            raise ValueError(f"Invalid language code(s): {', '.join(invalid[:4])}")
        return self


class ProjectJob(BaseModel):
    id: str
    name: str = "Preparing project…"
    request: ProjectGenerationRequest
    provider: Literal["openai"] = "openai"
    status: ProjectStatus = ProjectStatus.queued
    stage: str = "queued"
    progress: int = 0
    trend_score: float | None = None
    error: str | None = None
    created_at: str = Field(default_factory=utc_timestamp)
    updated_at: str = Field(default_factory=utc_timestamp)
    started_at: str | None = None
    completed_at: str | None = None
    result: dict | None = None

    @model_validator(mode="before")
    @classmethod
    def inherit_request_provider(cls, values):
        if isinstance(values, dict) and "provider" not in values:
            values["provider"] = "openai"
        return values


class BulkProjectDeleteRequest(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=200, alias="project_ids")
    confirm: str = Field(default="", max_length=20)

    @model_validator(mode="after")
    def normalize(self):
        ids = []
        for value in self.ids:
            item = (value or "").strip()
            if not item or not PROJECT_ID_PATTERN.fullmatch(item):
                raise ValueError(f"Invalid project id: {item[:120]}")
            ids.append(item)
        self.ids = list(dict.fromkeys(ids))
        if not self.ids:
            raise ValueError("project_ids must contain at least one valid id")
        return self
