from typing import Any
from pydantic import BaseModel, Field


class LanguageOutput(BaseModel):
    language: str
    title: str = ""
    outline: dict[str,Any] = Field(default_factory=dict)
    draft: str = ""
    final_text: str = ""
    checks: dict[str,Any] = Field(default_factory=dict)


class WorkflowResult(BaseModel):
    niche: str
    canonical_title: str = ""
    blueprint: dict[str,Any] = Field(default_factory=dict)
    research: dict[str,Any] = Field(default_factory=dict)
    outputs: dict[str,LanguageOutput] = Field(default_factory=dict)
