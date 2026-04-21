from __future__ import annotations

import json
import re
from collections import defaultdict

from backend.app.models import SanitizeResponse, SanitizationExample, SanitizationSummary
from backend.app.sanitizer.builtins import FIELD_CATEGORY_HINTS, LOGFMT_RE, REGEX_RULES, RegexRule


class SanitizerEngine:
    def sanitize(self, text: str, mode: str = "mask", preserve_correlation: bool = True) -> SanitizeResponse:
        tracker = _MatchTracker(mode=mode, preserve_correlation=preserve_correlation)
        sanitized_lines: list[str] = []
        transformed_lines = 0

        for line in text.splitlines(keepends=True):
            content = line.rstrip("\r\n")
            ending = line[len(content):]
            sanitized_content = self._sanitize_record(content, tracker)
            if sanitized_content != content:
                transformed_lines += 1
            sanitized_lines.append(sanitized_content + ending)

        summary = SanitizationSummary(
            total_lines=len([line for line in text.splitlines() if line.strip()]),
            transformed_lines=transformed_lines,
            total_matches=tracker.total_matches,
            categories=dict(sorted(tracker.category_counts.items())),
        )
        examples = [
            SanitizationExample(
                category=example["category"],
                original_preview=example["original_preview"],
                replacement_preview=example["replacement_preview"],
            )
            for example in tracker.examples
        ]
        return SanitizeResponse(
            summary=summary,
            sanitized_text="".join(sanitized_lines),
            examples=examples,
        )

    def _sanitize_record(self, record: str, tracker: "_MatchTracker") -> str:
        if not record.strip():
            return record

        json_sanitized = self._sanitize_json_record(record, tracker)
        if json_sanitized is not None:
            return json_sanitized

        logfmt_sanitized = self._sanitize_logfmt_record(record, tracker)
        if logfmt_sanitized is not None:
            return logfmt_sanitized

        return self._sanitize_text(record, tracker)

    def _sanitize_json_record(self, record: str, tracker: "_MatchTracker") -> str | None:
        try:
            payload = json.loads(record)
        except json.JSONDecodeError:
            return None
        sanitized = self._sanitize_json_value(payload, tracker, parent_key=None)
        return json.dumps(sanitized, ensure_ascii=False, separators=(",", ":"))

    def _sanitize_json_value(self, value: object, tracker: "_MatchTracker", parent_key: str | None) -> object:
        if isinstance(value, dict):
            return {
                key: self._sanitize_json_value(item, tracker, parent_key=key)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self._sanitize_json_value(item, tracker, parent_key=parent_key) for item in value]
        if isinstance(value, str):
            category = self._category_for_key(parent_key, value)
            if category:
                return tracker.replace(category, value)
            return self._sanitize_text(value, tracker)
        if parent_key and value is not None:
            category = self._category_for_key(parent_key, str(value))
            if category:
                return tracker.replace(category, str(value))
        return value

    def _sanitize_logfmt_record(self, record: str, tracker: "_MatchTracker") -> str | None:
        matches = list(LOGFMT_RE.finditer(record))
        if len(matches) < 2:
            return None

        cursor = 0
        for match in matches:
            if record[cursor:match.start()].strip():
                return None
            cursor = match.end()
        if record[cursor:].strip():
            return None

        rebuilt: list[str] = []
        cursor = 0
        for match in matches:
            rebuilt.append(self._sanitize_text(record[cursor:match.start()], tracker))

            key = match.group("key")
            original_value = match.group("value")
            quote = ""
            value = original_value
            if len(original_value) >= 2 and original_value[0] in {'"', "'"} and original_value[-1] == original_value[0]:
                quote = original_value[0]
                value = original_value[1:-1]

            category = self._category_for_key(key, value)
            sanitized_value = tracker.replace(category, value) if category else self._sanitize_text(value, tracker)
            if quote:
                sanitized_value = f"{quote}{sanitized_value}{quote}"
            rebuilt.append(f"{key}={sanitized_value}")
            cursor = match.end()

        rebuilt.append(self._sanitize_text(record[cursor:], tracker))
        return "".join(rebuilt)

    def _sanitize_text(self, text: str, tracker: "_MatchTracker") -> str:
        sanitized = text
        for rule in REGEX_RULES:
            sanitized = self._apply_rule(sanitized, rule, tracker)
        sanitized = self._sanitize_credit_cards(sanitized, tracker)
        return sanitized

    def _apply_rule(self, text: str, rule: RegexRule, tracker: "_MatchTracker") -> str:
        def replace_match(match: re.Match[str]) -> str:
            if rule.value_group:
                original = match.group(rule.value_group)
                replacement = tracker.replace(rule.category, original)
                prefix = match.groupdict().get("prefix")
                suffix = match.groupdict().get("suffix")
                if prefix is not None or suffix is not None:
                    return f"{prefix or ''}{replacement}{suffix or ''}"
                start, end = match.span(rule.value_group)
                relative_start = start - match.start()
                relative_end = end - match.start()
                matched_text = match.group(0)
                return matched_text[:relative_start] + replacement + matched_text[relative_end:]
            return tracker.replace(rule.category, match.group(0))

        return rule.pattern.sub(replace_match, text)

    def _sanitize_credit_cards(self, text: str, tracker: "_MatchTracker") -> str:
        def replace_match(match: re.Match[str]) -> str:
            original = match.group(0)
            digits_only = re.sub(r"\D", "", original)
            if len(digits_only) < 13 or len(digits_only) > 19:
                return original
            if not self._passes_luhn(digits_only):
                return original
            return tracker.replace("CREDIT_CARD", original)

        return re.sub(r"\b(?:\d[ -]?){13,19}\b", replace_match, text)

    def _passes_luhn(self, digits: str) -> bool:
        checksum = 0
        parity = len(digits) % 2
        for index, digit_char in enumerate(digits):
            digit = int(digit_char)
            if index % 2 == parity:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0

    def _category_for_key(self, key: str | None, value: str) -> str | None:
        if not key:
            return None
        normalized_key = key.lower().replace("-", "_")
        hinted = FIELD_CATEGORY_HINTS.get(normalized_key)
        if hinted == "URL":
            return "URL" if re.match(r"^https?://", value, re.IGNORECASE) else "HOSTNAME"
        if hinted == "HOSTNAME":
            if re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$", value):
                return "IP_ADDRESS"
            return "HOSTNAME"
        return hinted


class _MatchTracker:
    def __init__(self, mode: str, preserve_correlation: bool) -> None:
        self.mode = mode
        self.preserve_correlation = preserve_correlation
        self.total_matches = 0
        self.category_counts: dict[str, int] = defaultdict(int)
        self.examples: list[dict[str, str]] = []
        self._example_counts: dict[str, int] = defaultdict(int)
        self._correlation_ids: dict[tuple[str, str], str] = {}
        self._correlation_sequence: dict[str, int] = defaultdict(int)

    def replace(self, category: str, original: str) -> str:
        replacement = self._replacement_for(category, original)
        self.total_matches += 1
        self.category_counts[category] += 1
        if self._example_counts[category] < 3:
            self.examples.append(
                {
                    "category": category,
                    "original_preview": self._preview(original),
                    "replacement_preview": replacement,
                }
            )
            self._example_counts[category] += 1
        return replacement

    def _replacement_for(self, category: str, original: str) -> str:
        if self.mode == "hash":
            return f"<{category}:{self._short_hash(original)}>"
        if self.preserve_correlation:
            key = (category, original)
            if key not in self._correlation_ids:
                self._correlation_sequence[category] += 1
                self._correlation_ids[key] = str(self._correlation_sequence[category])
            return f"<{category}:{self._correlation_ids[key]}>"
        return f"<{category}>"

    def _short_hash(self, value: str) -> str:
        import hashlib

        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]

    def _preview(self, value: str) -> str:
        if len(value) <= 4:
            return "***"
        return f"{value[:2]}***{value[-2:]}"
