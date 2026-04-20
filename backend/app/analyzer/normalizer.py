from __future__ import annotations

import re

from backend.app.models import LogEntry


ERROR_LEVELS = {"WARNING", "ERROR", "FATAL", "CRITICAL"}
ERROR_WORD_RE = re.compile(
    r"\b(error|exception|failed|failure|timeout|timed out|refused|denied|forbidden|unauthorized|oomkilled|bad gateway|crashloopbackoff|deadlock|no space left|too many connections|certificate|x509)\b",
    re.IGNORECASE,
)


class LogNormalizer:
    replacements: tuple[tuple[re.Pattern[str], str], ...] = (
        (re.compile(r"https?://[^\s\"']+", re.IGNORECASE), "<URL>"),
        (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE), "<UUID>"),
        (re.compile(r"\btrace[_-]?id[:=]\w[\w.\-]*", re.IGNORECASE), "trace_id=<ID>"),
        (re.compile(r"\bspan[_-]?id[:=]\w[\w.\-]*", re.IGNORECASE), "span_id=<ID>"),
        (re.compile(r"\bcorrelation[_-]?id[:=]\w[\w.\-]*", re.IGNORECASE), "correlation_id=<ID>"),
        (re.compile(r"\brequest[_-]?id[:=]\w[\w.\-]*", re.IGNORECASE), "request_id=<ID>"),
        (re.compile(r"\buser[_-]?id[:=]\w[\w.\-]*", re.IGNORECASE), "user_id=<ID>"),
        (re.compile(r"\b(?:req|txn|tx|session|client|order|bet)-[A-Za-z0-9_.-]+\b", re.IGNORECASE), "<ID>"),
        (re.compile(r"\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?\b"), "<TIMESTAMP>"),
        (re.compile(r"\b\d{1,2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}\s+[+\-]\d{4}\b"), "<TIMESTAMP>"),
        (re.compile(r"\b[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b"), "<TIMESTAMP>"),
        (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "<DATE>"),
        (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b"), "<IP>:<PORT>"),
        (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<IP>"),
        (re.compile(r"\b(?:[a-z0-9](?:[-a-z0-9]*[a-z0-9])?\.)+[a-z][a-z0-9-]{1,}(?::\d{2,5})?\b", re.IGNORECASE), "<HOST>"),
        (re.compile(r"(?<=/)\d{2,}(?=/|$)"), "<NUMBER>"),
        (re.compile(r"\b\d+(?:\.\d+)?(?:ms|s|sec|msec|seconds)\b", re.IGNORECASE), "<DURATION>"),
        (re.compile(r"\b\d+(?:\.\d+)?(?:KiB|MiB|GiB|KB|MB|GB|bytes)\b", re.IGNORECASE), "<SIZE>"),
        (re.compile(r"\b[0-9a-f]{16,}\b", re.IGNORECASE), "<HEX>"),
        (re.compile(r"(?i)\b(request|trace|span|correlation|session|user|client|order|bet)[-_ ]?id[:=][\w.\-]+"), r"\1_id=<ID>"),
        (re.compile(r"(?i)\b(id|uid)=\w[\w.\-]*"), r"\1=<ID>"),
        (re.compile(r"\b\d{4,}\b"), "<NUMBER>"),
    )

    def normalize(self, entries: list[LogEntry]) -> list[LogEntry]:
        normalized_entries: list[LogEntry] = []
        for entry in entries:
            normalized_message = self.normalize_message(entry.message)
            normalized_entries.append(entry.model_copy(update={"normalized_message": normalized_message}))
        return normalized_entries

    def normalize_message(self, message: str) -> str:
        normalized = message.strip()
        for pattern, replacement in self.replacements:
            normalized = pattern.sub(replacement, normalized)
        normalized = re.sub(r"(?m)^\s+at\s+[\w.$_]+\(.*?\)$", " at <STACK_FRAME>", normalized)
        normalized = re.sub(r"(?m)^File \".*?\", line \d+, in .*$", "File <PYTHON_FRAME>", normalized)
        normalized = re.sub(r"(?m)^\s*\.\.\. \d+ more$", "... <STACK_FRAMES> more", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def extract_error_entries(self, entries: list[LogEntry]) -> list[LogEntry]:
        return [
            entry
            for entry in entries
            if entry.level in ERROR_LEVELS or ERROR_WORD_RE.search(entry.message)
        ]
