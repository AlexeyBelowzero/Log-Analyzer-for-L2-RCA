from __future__ import annotations

import json
import re
from typing import Any

from backend.app.models import LogEntry


LOGFMT_RE = re.compile(r"(?P<key>[A-Za-z_][\w.\-]*)=(?P<value>\"[^\"]*\"|'[^']*'|[^\s]+)")
LEVEL_RE = re.compile(
    r"\b(TRACE|DEBUG|INFO|NOTICE|WARN|WARNING|ERROR|ERR|FATAL|CRITICAL|CRIT|ALERT|EMERG)\b",
    re.IGNORECASE,
)
WEB_ACCESS_RE = re.compile(
    r"^(?P<remote_addr>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+"
    r'"(?P<method>[A-Z]+)\s+(?P<path>\S+)(?:\s+HTTP/(?P<http_version>[^"]+))?"\s+'
    r"(?P<status>\d{3})\s+(?P<body_bytes_sent>\S+)"
)
NGINX_ERROR_RE = re.compile(
    r"^(?P<timestamp>\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"\[(?P<level>\w+)\]\s+(?P<pid>\d+)#(?P<tid>\d+):\s+(?P<message>.*)$",
    re.IGNORECASE,
)
CRI_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)\s+"
    r"(?P<stream>stdout|stderr)\s+(?P<flag>[FP])\s+(?P<message>.*)$"
)
SYSLOG_RFC3164_RE = re.compile(
    r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+(?P<process>[\w.\-/]+)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.*)$"
)
SYSLOG_RFC5424_RE = re.compile(
    r"^<(?P<priority>\d+)>\d+\s+(?P<timestamp>\S+)\s+(?P<host>\S+)\s+"
    r"(?P<app>\S+)\s+(?P<procid>\S+)\s+(?P<msgid>\S+)\s+(?:-|\[[^\]]+\])\s+(?P<message>.*)$"
)
POSTGRES_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\s+\w+)?)\s+"
    r"\[(?P<pid>\d+)\]\s+(?P<level>[A-Z]+):\s+(?P<message>.*)$"
)
MYSQL_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\s+"
    r"(?P<thread>\d+)\s+\[(?P<level>\w+)\]\s+(?:\[[^\]]+\]\s+)?(?:\[[^\]]+\]\s+)?(?P<message>.*)$",
    re.IGNORECASE,
)
REDIS_RE = re.compile(
    r"^(?P<pid>\d+):(?P<role>[A-Z])\s+(?P<timestamp>\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+"
    r"(?P<marker>[#*\-.])\s+(?P<message>.*)$"
)
JAVA_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[,.]\d+)?)\s+"
    r"(?P<level>TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\s+"
    r"(?P<context>.*?)\s+-\s+(?P<message>.*)$",
    re.IGNORECASE,
)
SPRING_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\s+"
    r"(?P<level>TRACE|DEBUG|INFO|WARN|ERROR|FATAL)\s+\d+\s+---\s+\[(?P<thread>[^\]]+)\]\s+"
    r"(?P<logger>\S+)\s+:\s+(?P<message>.*)$",
    re.IGNORECASE,
)
PYTHON_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d+)?)\s+"
    r"(?:-\s+)?(?P<logger>[\w.\-/]+)?\s*-?\s*"
    r"(?P<level>DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\s*-?\s*(?P<message>.*)$",
    re.IGNORECASE,
)
ISO_LEVEL_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:[,.]\d+)?Z?)\s+"
    r"(?P<level>TRACE|DEBUG|INFO|NOTICE|WARN|WARNING|ERROR|ERR|FATAL|CRITICAL)\s+(?P<message>.*)$",
    re.IGNORECASE,
)


class LogParser:
    def parse(self, raw_text: str, source_type: str = "auto") -> list[LogEntry]:
        return [self.parse_line(record, source_type) for record in self._coalesce_records(raw_text)]

    def parse_line(self, record: str, source_type: str = "auto") -> LogEntry:
        parsers = {
            "json": self._parse_json,
            "docker_json": self._parse_json,
            "cri": self._parse_cri,
            "logfmt": self._parse_logfmt,
            "web_access": self._parse_web_access,
            "nginx_error": self._parse_nginx_error,
            "syslog": self._parse_syslog,
            "postgres": self._parse_postgres,
            "mysql": self._parse_mysql,
            "redis": self._parse_redis,
            "java": self._parse_java,
            "python": self._parse_python,
            "plain": self._parse_plain,
        }
        if source_type != "auto":
            return parsers.get(source_type, self._parse_plain)(record) or self._parse_plain(record)

        for parser in (
            self._parse_json,
            self._parse_cri,
            self._parse_nginx_error,
            self._parse_web_access,
            self._parse_syslog,
            self._parse_postgres,
            self._parse_mysql,
            self._parse_redis,
            self._parse_spring,
            self._parse_java,
            self._parse_python,
            self._parse_iso_level,
            self._parse_logfmt,
        ):
            entry = parser(record)
            if entry:
                return entry
        return self._parse_plain(record)

    def _coalesce_records(self, raw_text: str) -> list[str]:
        records: list[str] = []
        current: list[str] = []
        for raw_line in raw_text.splitlines():
            line = raw_line.rstrip()
            if not line.strip():
                continue
            if not current:
                current = [line]
                continue
            if self._is_continuation(line):
                current.append(line)
            else:
                records.append("\n".join(current))
                current = [line]
        if current:
            records.append("\n".join(current))
        return records

    def _is_continuation(self, line: str) -> bool:
        stripped = line.strip()
        return bool(
            line.startswith((" ", "\t"))
            or re.match(r"^(at\s+|Caused by:|Suppressed:|Traceback \(most recent call last\):|File \"|During handling|The above exception|\.\.\. \d+ more)", stripped)
            or re.match(r"^(DETAIL|HINT|STATEMENT|CONTEXT|QUERY):\s+", stripped)
        )

    def _parse_json(self, record: str) -> LogEntry | None:
        first_line = record.splitlines()[0].strip()
        try:
            payload = json.loads(first_line)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None

        if "log" in payload and ("stream" in payload or "time" in payload):
            return self._parse_docker_json(record, payload)

        level = self._get_first(payload, ("log.level", "level", "severity", "severity_text", "status.level", "event.severity")) or "INFO"
        service = self._get_first(
            payload,
            (
                "service.name",
                "service",
                "app.name",
                "app",
                "application",
                "logger",
                "log.logger",
                "kubernetes.container.name",
                "kubernetes.container_name",
                "kubernetes.labels.app",
                "container.name",
                "container_name",
                "pod",
                "job",
            ),
        )
        timestamp = self._get_first(payload, ("@timestamp", "timestamp", "time", "ts", "datetime", "event.created", "observedTimestamp"))
        message = self._get_first(
            payload,
            (
                "message",
                "msg",
                "error.message",
                "error",
                "event.original",
                "log",
                "body",
                "textPayload",
                "jsonPayload.message",
            ),
        )
        status = self._get_first(
            payload,
            (
                "http.response.status_code",
                "http.status_code",
                "response.status",
                "response.status_code",
                "status",
                "status_code",
            ),
        )
        level = self._level_from_status(status) or self._normalize_level(level)
        message_text = self._stringify_message(message, first_line)

        stack = self._get_first(payload, ("error.stack_trace", "stacktrace", "stack_trace", "exception.stacktrace", "exc_info"))
        if stack:
            message_text = f"{message_text}\n{self._stringify_message(stack, '')}".strip()

        if len(record.splitlines()) > 1:
            message_text = f"{message_text}\n" + "\n".join(record.splitlines()[1:])

        return LogEntry(
            raw=record,
            message=message_text,
            level=level,
            service=str(service) if service is not None else None,
            timestamp=str(timestamp) if timestamp is not None else None,
            source_type="json",
            fields=payload,
        )

    def _parse_docker_json(self, record: str, payload: dict[str, Any]) -> LogEntry:
        inner = str(payload.get("log", "")).rstrip("\n")
        inner_entry = self.parse_line(inner, "auto") if inner and inner != record else None
        stream = str(payload.get("stream", "stdout"))
        if inner_entry and inner_entry.source_type != "plain":
            level = inner_entry.level
            service = inner_entry.service
            message = inner_entry.message
            fields = {**payload, "inner": inner_entry.fields}
        else:
            level = self._infer_level(inner)
            if level == "INFO" and stream == "stderr":
                level = "ERROR"
            service = None
            message = inner or record
            fields = payload

        return LogEntry(
            raw=record,
            message=message,
            level=level,
            service=service,
            timestamp=str(payload.get("time")) if payload.get("time") is not None else None,
            source_type="docker_json",
            fields=fields,
        )

    def _parse_cri(self, record: str) -> LogEntry | None:
        match = CRI_RE.match(record.splitlines()[0])
        if not match:
            return None
        payload = match.group("message")
        inner_entry = self.parse_line(payload, "auto") if payload else None
        level = inner_entry.level if inner_entry else self._infer_level(payload)
        if level == "INFO" and match.group("stream") == "stderr":
            level = "ERROR"
        message = inner_entry.message if inner_entry else payload
        if len(record.splitlines()) > 1:
            message = f"{message}\n" + "\n".join(record.splitlines()[1:])
        return LogEntry(
            raw=record,
            message=message,
            level=level,
            service=inner_entry.service if inner_entry else None,
            timestamp=match.group("timestamp"),
            source_type="cri",
            fields=match.groupdict(),
        )

    def _parse_logfmt(self, record: str) -> LogEntry | None:
        first_line = record.splitlines()[0]
        pairs: dict[str, str] = {}
        for match in LOGFMT_RE.finditer(first_line):
            value = match.group("value")
            if len(value) >= 2 and value[0] in {'"', "'"} and value[-1] == value[0]:
                value = value[1:-1]
            pairs[match.group("key")] = value

        if len(pairs) < 2:
            return None

        level = pairs.get("level") or pairs.get("severity") or pairs.get("at") or "INFO"
        status = pairs.get("status") or pairs.get("status_code") or pairs.get("http_status")
        level = self._level_from_status(status) or self._normalize_level(level)
        message = pairs.get("message") or pairs.get("msg") or pairs.get("error") or pairs.get("err")
        if not message and status and (pairs.get("method") or pairs.get("path")):
            message = f"HTTP {status} {pairs.get('method', '').strip()} {pairs.get('path', '').strip()}".strip()
        if not message:
            message = first_line
        if len(record.splitlines()) > 1:
            message = f"{message}\n" + "\n".join(record.splitlines()[1:])

        service = self._first_non_duration(
            pairs.get("service_name"),
            pairs.get("app"),
            pairs.get("application"),
            pairs.get("logger"),
            pairs.get("container"),
            pairs.get("service"),
        )

        return LogEntry(
            raw=record,
            message=message,
            level=level,
            service=service,
            timestamp=pairs.get("timestamp") or pairs.get("time") or pairs.get("ts"),
            source_type="logfmt",
            fields=pairs,
        )

    def _parse_web_access(self, record: str) -> LogEntry | None:
        match = WEB_ACCESS_RE.match(record.splitlines()[0])
        if not match:
            return None
        fields = match.groupdict()
        status = fields["status"]
        method = fields["method"]
        path = fields["path"]
        return LogEntry(
            raw=record,
            message=f"HTTP {status} {method} {path}",
            level=self._level_from_status(status) or "INFO",
            service="web",
            timestamp=fields["timestamp"],
            source_type="web_access",
            fields=fields,
        )

    def _parse_nginx_error(self, record: str) -> LogEntry | None:
        match = NGINX_ERROR_RE.match(record.splitlines()[0])
        if not match:
            return None
        message = match.group("message")
        if len(record.splitlines()) > 1:
            message = f"{message}\n" + "\n".join(record.splitlines()[1:])
        return LogEntry(
            raw=record,
            message=message,
            level=self._normalize_level(match.group("level")),
            service="nginx",
            timestamp=match.group("timestamp"),
            source_type="nginx_error",
            fields=match.groupdict(),
        )

    def _parse_syslog(self, record: str) -> LogEntry | None:
        first_line = record.splitlines()[0]
        match = SYSLOG_RFC5424_RE.match(first_line)
        if match:
            level = self._level_from_priority(match.group("priority"))
            return self._entry_from_match(record, match.group("message"), level, match.group("app"), "syslog", match.group("timestamp"), match.groupdict())

        match = SYSLOG_RFC3164_RE.match(first_line)
        if not match:
            return None
        return self._entry_from_match(
            record,
            match.group("message"),
            self._infer_level(match.group("message")),
            match.group("process"),
            "syslog",
            match.group("timestamp"),
            match.groupdict(),
        )

    def _parse_postgres(self, record: str) -> LogEntry | None:
        match = POSTGRES_RE.match(record.splitlines()[0])
        if not match:
            return None
        message = match.group("message")
        if len(record.splitlines()) > 1:
            message = f"{message}\n" + "\n".join(record.splitlines()[1:])
        return LogEntry(
            raw=record,
            message=message,
            level=self._normalize_level(match.group("level")),
            service="postgres",
            timestamp=match.group("timestamp"),
            source_type="postgres",
            fields=match.groupdict(),
        )

    def _parse_mysql(self, record: str) -> LogEntry | None:
        match = MYSQL_RE.match(record.splitlines()[0])
        if not match:
            return None
        return self._entry_from_match(record, match.group("message"), match.group("level"), "mysql", "mysql", match.group("timestamp"), match.groupdict())

    def _parse_redis(self, record: str) -> LogEntry | None:
        match = REDIS_RE.match(record.splitlines()[0])
        if not match:
            return None
        marker = match.group("marker")
        level = "WARNING" if marker == "#" else "INFO"
        message = match.group("message")
        if re.search(r"\berror|fail|oom|denied\b", message, re.IGNORECASE):
            level = "ERROR"
        return self._entry_from_match(record, message, level, "redis", "redis", match.group("timestamp"), match.groupdict())

    def _parse_spring(self, record: str) -> LogEntry | None:
        match = SPRING_RE.match(record.splitlines()[0])
        if not match:
            return None
        return self._entry_from_match(record, match.group("message"), match.group("level"), match.group("logger"), "java", match.group("timestamp"), match.groupdict())

    def _parse_java(self, record: str) -> LogEntry | None:
        match = JAVA_RE.match(record.splitlines()[0])
        if not match:
            return None
        return self._entry_from_match(record, match.group("message"), match.group("level"), self._service_from_context(match.group("context")), "java", match.group("timestamp"), match.groupdict())

    def _parse_python(self, record: str) -> LogEntry | None:
        match = PYTHON_RE.match(record.splitlines()[0])
        if not match:
            return None
        return self._entry_from_match(record, match.group("message"), match.group("level"), match.group("logger"), "python", match.group("timestamp"), match.groupdict())

    def _parse_iso_level(self, record: str) -> LogEntry | None:
        match = ISO_LEVEL_RE.match(record.splitlines()[0])
        if not match:
            return None
        return self._entry_from_match(record, match.group("message"), match.group("level"), None, "plain", match.group("timestamp"), match.groupdict())

    def _parse_plain(self, record: str) -> LogEntry:
        first_line = record.splitlines()[0]
        level_match = LEVEL_RE.search(first_line)
        level = level_match.group(1) if level_match else self._infer_level(record)
        service = self._extract_bracketed_service(first_line)
        return LogEntry(
            raw=record,
            message=record,
            level=self._normalize_level(level),
            service=service,
            source_type="plain",
            fields={},
        )

    def _entry_from_match(
        self,
        record: str,
        message: str,
        level: object,
        service: str | None,
        source_type: str,
        timestamp: str | None,
        fields: dict[str, Any],
    ) -> LogEntry:
        if len(record.splitlines()) > 1:
            message = f"{message}\n" + "\n".join(record.splitlines()[1:])
        return LogEntry(
            raw=record,
            message=message,
            level=self._normalize_level(level),
            service=service,
            timestamp=timestamp,
            source_type=source_type,
            fields=fields,
        )

    def _get_first(self, payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
        for key in keys:
            if key in payload and payload[key] is not None:
                return payload[key]
            value = self._get_nested(payload, key)
            if value is not None:
                return value
        return None

    def _get_nested(self, payload: dict[str, Any], dotted_key: str) -> Any:
        current: Any = payload
        for part in dotted_key.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    def _level_from_status(self, status: object) -> str | None:
        try:
            numeric_status = int(str(status))
        except (TypeError, ValueError):
            return None
        if numeric_status >= 500:
            return "ERROR"
        if numeric_status >= 400:
            return "WARNING"
        return "INFO"

    def _level_from_priority(self, priority: object) -> str:
        try:
            severity = int(str(priority)) % 8
        except ValueError:
            return "INFO"
        if severity <= 2:
            return "CRITICAL"
        if severity == 3:
            return "ERROR"
        if severity == 4:
            return "WARNING"
        return "INFO"

    def _normalize_level(self, level: object) -> str:
        normalized = str(level).upper()
        aliases = {
            "WARN": "WARNING",
            "ERR": "ERROR",
            "CRIT": "CRITICAL",
            "ALERT": "CRITICAL",
            "EMERG": "CRITICAL",
            "SEVERE": "ERROR",
        }
        return aliases.get(normalized, normalized)

    def _infer_level(self, message: str) -> str:
        level_match = LEVEL_RE.search(message)
        if level_match:
            return self._normalize_level(level_match.group(1))
        if re.search(r"\b(exception|failed|failure|timeout|refused|denied|oom|panic|deadlock|502|503|504)\b", message, re.IGNORECASE):
            return "ERROR"
        return "INFO"

    def _extract_bracketed_service(self, line: str) -> str | None:
        match = re.search(r"\[([A-Za-z][\w.\-]{1,80})\]", line)
        return match.group(1) if match else None

    def _service_from_context(self, context: str) -> str | None:
        bracketed = self._extract_bracketed_service(context)
        if bracketed:
            return bracketed
        tokens = [token for token in re.split(r"\s+", context.strip()) if token]
        return tokens[-1] if tokens and "." in tokens[-1] else None

    def _first_non_duration(self, *values: str | None) -> str | None:
        for value in values:
            if value and not re.match(r"^\d+(?:\.\d+)?(?:ms|s|m|h)$", value):
                return value
        return None

    def _stringify_message(self, message: Any, fallback: str) -> str:
        if message is None:
            return fallback
        if isinstance(message, str):
            return message
        return json.dumps(message, ensure_ascii=False, sort_keys=True)
