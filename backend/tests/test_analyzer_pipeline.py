from pathlib import Path

from backend.app.analyzer.classifier import ErrorClassifier
from backend.app.analyzer.deduplicator import ErrorDeduplicator
from backend.app.analyzer.engine import LogAnalyzer
from backend.app.analyzer.normalizer import LogNormalizer
from backend.app.analyzer.parser import LogParser


def test_parse_ecs_json_log_with_nested_fields() -> None:
    parser = LogParser()
    line = (
        '{"@timestamp":"2026-04-20T10:15:01Z","log":{"level":"error","logger":"payment.api"},'
        '"service":{"name":"payment-api"},"message":"Connection refused to upstream 10.1.2.3:8080"}'
    )

    entry = parser.parse_line(line)

    assert entry.source_type == "json"
    assert entry.timestamp == "2026-04-20T10:15:01Z"
    assert entry.level == "ERROR"
    assert entry.service == "payment-api"
    assert entry.message == "Connection refused to upstream 10.1.2.3:8080"


def test_parse_logfmt_nginx_error_web_access_and_plain_fallback() -> None:
    parser = LogParser()

    logfmt = parser.parse_line('ts=2026-04-20T10:15:05Z level=error app=checkout msg="SQL timeout on checkout"')
    nginx_error = parser.parse_line('2026/04/20 10:15:06 [error] 123#123: *456 connect() failed (111: Connection refused) while connecting to upstream')
    access = parser.parse_line('10.0.0.10 - - [20/Apr/2026:10:15:10 +0000] "POST /api/pay/782918 HTTP/1.1" 502 180 "-" "curl/8.0"')
    plain = parser.parse_line("2026-04-20 10:15:12 [worker] FATAL OOMKilled: container reached memory limit")

    assert logfmt.source_type == "logfmt"
    assert logfmt.message == "SQL timeout on checkout"
    assert nginx_error.source_type == "nginx_error"
    assert nginx_error.level == "ERROR"
    assert access.source_type == "web_access"
    assert access.level == "ERROR"
    assert access.message == "HTTP 502 POST /api/pay/782918"
    assert plain.source_type == "plain"
    assert plain.level == "FATAL"
    assert plain.service == "worker"


def test_parse_docker_cri_postgres_java_python_syslog() -> None:
    parser = LogParser()

    docker = parser.parse_line('{"log":"{\\"level\\":\\"error\\",\\"service\\":\\"api\\",\\"message\\":\\"deadline exceeded\\"}\\n","stream":"stderr","time":"2026-04-20T10:15:01.123Z"}')
    cri = parser.parse_line('2026-04-20T10:15:02.123456789Z stderr F level=error app=api msg="lookup redis.default.svc no such host"')
    postgres = parser.parse_line("2026-04-20 10:15:03 UTC [12345] ERROR:  deadlock detected")
    java = parser.parse_line("2026-04-20 10:15:04,222 ERROR [payment-api] c.e.PaymentService - NullPointerException while placing bet")
    python = parser.parse_line("2026-04-20 10:15:05,333 payment.api ERROR RuntimeError: upstream timeout")
    syslog = parser.parse_line("Apr 20 10:15:06 node-1 kubelet[1234]: Back-off restarting failed container payment-api")

    assert docker.source_type == "docker_json"
    assert docker.level == "ERROR"
    assert docker.service == "api"
    assert cri.source_type == "cri"
    assert cri.service == "api"
    assert postgres.source_type == "postgres"
    assert java.source_type == "java"
    assert python.source_type == "python"
    assert syslog.source_type == "syslog"
    assert syslog.level == "ERROR"


def test_multiline_stack_trace_is_one_record() -> None:
    parser = LogParser()
    logs = "\n".join(
        [
            "2026-04-20 10:15:04,222 ERROR [payment-api] c.e.PaymentService - NullPointerException while placing bet",
            "    at com.example.PaymentService.place(PaymentService.java:42)",
            "    at com.example.Controller.handle(Controller.java:18)",
            "Caused by: java.lang.IllegalStateException: missing odds",
        ]
    )

    entries = parser.parse(logs)

    assert len(entries) == 1
    assert entries[0].source_type == "java"
    assert "PaymentService.java:42" in entries[0].message


def test_normalizer_replaces_dynamic_values_but_keeps_status_codes() -> None:
    normalizer = LogNormalizer()
    message = "HTTP 502 from 10.1.2.3:8080 request_id=req-1001 user_id=782918 at 2026-04-20T10:15:01Z /api/pay/782918 took 123ms"

    normalized = normalizer.normalize_message(message)

    assert "HTTP 502" in normalized
    assert "<IP>:<PORT>" in normalized
    assert "request_id=<ID>" in normalized
    assert "user_id=<ID>" in normalized
    assert "<TIMESTAMP>" in normalized
    assert "/api/pay/<NUMBER>" in normalized
    assert "<DURATION>" in normalized


def test_grouping_merges_same_error_with_different_ips() -> None:
    analyzer = LogAnalyzer()
    logs = "\n".join(
        [
            '{"level":"ERROR","service":"bettingservice","message":"Connection refused to upstream 10.1.2.3:8080"}',
            '{"level":"ERROR","service":"bettingservice","message":"Connection refused to upstream 10.1.2.4:8080"}',
            '{"level":"ERROR","service":"bettingservice","message":"Connection refused to upstream 10.1.2.5:8080"}',
        ]
    )

    result = analyzer.analyze(logs)

    assert result.summary.error_events == 3
    assert result.summary.unique_patterns == 1
    assert result.summary.dominant_percentage == 100
    assert result.groups[0].pattern == "Connection refused to upstream <IP>:<PORT>"
    assert result.groups[0].classification == "NETWORK_ERROR"


def test_classifier_marks_unknown_when_no_rule_matches() -> None:
    parser = LogParser()
    normalizer = LogNormalizer()
    deduplicator = ErrorDeduplicator()
    classifier = ErrorClassifier()

    entries = parser.parse('{"level":"ERROR","service":"api","message":"Unexpected payment state transition"}')
    groups = deduplicator.group(normalizer.extract_error_entries(normalizer.normalize(entries)))
    classified = classifier.classify(groups)

    assert classified[0].classification == "UNKNOWN"


def test_sample_log_corpus_produces_multiple_rca_classes() -> None:
    sample_path = Path("samples/rca_mixed_test_logs.log")
    result = LogAnalyzer().analyze(sample_path.read_text(encoding="utf-8"), max_groups=30)
    classifications = {group.classification for group in result.groups}

    assert result.summary.total_lines > result.summary.parsed_lines
    assert result.summary.error_events >= 18
    assert "NETWORK_ERROR" in classifications
    assert "GATEWAY_ERROR" in classifications
    assert "DATABASE_ERROR" in classifications
    assert "APPLICATION_ERROR" in classifications
    assert "KUBERNETES_ERROR" in classifications
    assert "RESOURCE_EXHAUSTION" in classifications
    assert "TLS_CERTIFICATE_ERROR" in classifications
