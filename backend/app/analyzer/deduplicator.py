from __future__ import annotations

from collections import defaultdict

from backend.app.models import ErrorGroup, LogEntry


SEVERITY_RANK = {
    "INFO": 0,
    "WARNING": 1,
    "ERROR": 2,
    "FATAL": 3,
    "CRITICAL": 4,
}


class ErrorDeduplicator:
    def group(self, entries: list[LogEntry]) -> list[ErrorGroup]:
        grouped: dict[str, list[LogEntry]] = defaultdict(list)
        for entry in entries:
            key = (entry.normalized_message or entry.message).lower()
            grouped[key].append(entry)

        groups: list[ErrorGroup] = []
        for group_entries in grouped.values():
            pattern = group_entries[0].normalized_message or group_entries[0].message
            service = self._common_service(group_entries)
            level = max(group_entries, key=lambda item: SEVERITY_RANK.get(item.level, 0)).level
            groups.append(
                ErrorGroup(
                    pattern=pattern,
                    count=len(group_entries),
                    level=level,
                    service=service,
                    source_type=self._common_source_type(group_entries),
                    classification="UNKNOWN",
                    examples=[entry.raw for entry in group_entries[:3]],
                )
            )

        return sorted(groups, key=lambda group: (-group.count, group.pattern.lower()))

    def _common_service(self, entries: list[LogEntry]) -> str | None:
        services = {entry.service for entry in entries if entry.service}
        if len(services) == 1:
            return next(iter(services))
        if len(services) > 1:
            return "multiple"
        return None

    def _common_source_type(self, entries: list[LogEntry]) -> str | None:
        source_types = {entry.source_type for entry in entries if entry.source_type}
        if len(source_types) == 1:
            return next(iter(source_types))
        if len(source_types) > 1:
            return "multiple"
        return None
