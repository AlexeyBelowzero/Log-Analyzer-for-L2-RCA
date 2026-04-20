from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


SourceType = Literal[
    "auto",
    "json",
    "docker_json",
    "cri",
    "logfmt",
    "web_access",
    "nginx_error",
    "syslog",
    "postgres",
    "mysql",
    "redis",
    "java",
    "python",
    "plain",
]


class LogEntry(BaseModel):
    raw: str
    message: str
    normalized_message: str | None = None
    level: str = "INFO"
    service: str | None = None
    timestamp: str | None = None
    source_type: str = "plain"
    fields: dict[str, object] = Field(default_factory=dict)


class ErrorGroup(BaseModel):
    pattern: str
    count: int
    level: str
    service: str | None = None
    source_type: str | None = None
    classification: str
    examples: list[str] = Field(default_factory=list)


class Insight(BaseModel):
    title: str
    classification: str
    possible_causes: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class AnalysisSummary(BaseModel):
    total_lines: int
    parsed_lines: int
    error_events: int
    unique_patterns: int
    dominant_issue: str | None = None
    dominant_percentage: float = 0
    source_types: dict[str, int] = Field(default_factory=dict)


class AnalyzeRequest(BaseModel):
    text: str = Field(..., max_length=2_000_000)
    source_type: SourceType = "auto"
    max_groups: int = Field(default=10, ge=1, le=50)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Log text must not be empty.")
        return value


class AnalyzeResponse(BaseModel):
    summary: AnalysisSummary
    groups: list[ErrorGroup] = Field(default_factory=list)
    insights: list[Insight] = Field(default_factory=list)
