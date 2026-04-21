import json
from pathlib import Path

from backend.app.sanitizer.engine import SanitizerEngine


def test_sanitizer_masks_plain_text_sensitive_values() -> None:
    engine = SanitizerEngine()
    text = (
        "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def\n"
        "user_email=alex@example.com client_ip=10.42.1.15 password=supersecret\n"
    )

    result = engine.sanitize(text, mode="mask", preserve_correlation=False)

    assert result.summary.total_matches >= 4
    assert "alex@example.com" not in result.sanitized_text
    assert "10.42.1.15" not in result.sanitized_text
    assert "supersecret" not in result.sanitized_text
    assert "<BEARER_TOKEN>" in result.sanitized_text or "<JWT>" in result.sanitized_text
    assert result.summary.categories["EMAIL"] == 1
    assert result.summary.categories["IP_ADDRESS"] == 1


def test_sanitizer_preserves_correlation_in_mask_mode() -> None:
    engine = SanitizerEngine()
    text = '{"user_email":"alex@example.com","backup_email":"alex@example.com"}'

    result = engine.sanitize(text, mode="mask", preserve_correlation=True)
    payload = json.loads(result.sanitized_text)

    assert payload["user_email"] == payload["backup_email"]
    assert payload["user_email"].startswith("<EMAIL:")


def test_sanitizer_hash_mode_keeps_json_valid() -> None:
    engine = SanitizerEngine()
    text = '{"authorization":"Bearer abc.def.ghi","request_id":"req-123","password":"secret"}'

    result = engine.sanitize(text, mode="hash", preserve_correlation=True)
    payload = json.loads(result.sanitized_text)

    assert payload["authorization"].startswith("<BEARER_TOKEN:")
    assert payload["request_id"].startswith("<REQUEST_ID:")
    assert payload["password"].startswith("<PASSWORD:")


def test_sanitizer_handles_logfmt_records() -> None:
    engine = SanitizerEngine()
    text = 'level=error email="alex@example.com" request_id=req-123 token=abcd1234'

    result = engine.sanitize(text, mode="mask", preserve_correlation=False)

    assert 'email="<EMAIL>"' in result.sanitized_text
    assert "request_id=<REQUEST_ID>" in result.sanitized_text
    assert "token=<API_KEY>" in result.sanitized_text


def test_sanitizer_preserves_plain_text_keys_for_ids() -> None:
    engine = SanitizerEngine()
    text = "client_ip=10.42.1.15 session_id=sess-778899 request_id=req-123 user_id=99121"

    result = engine.sanitize(text, mode="mask", preserve_correlation=False)

    assert "client_ip=<IP_ADDRESS>" in result.sanitized_text
    assert "session_id=<SESSION_ID>" in result.sanitized_text
    assert "request_id=<REQUEST_ID>" in result.sanitized_text
    assert "user_id=<USER_ID>" in result.sanitized_text


def test_sanitizer_sample_corpus_detects_multiple_categories() -> None:
    sample_path = Path("samples/sanitizer_sensitive_test_logs.log")
    result = SanitizerEngine().sanitize(sample_path.read_text(encoding="utf-8"))

    assert result.summary.total_matches >= 10
    assert result.summary.categories["EMAIL"] >= 2
    assert result.summary.categories.get("JWT", 0) >= 1 or result.summary.categories.get("BEARER_TOKEN", 0) >= 1
    assert result.summary.categories["IP_ADDRESS"] >= 1
    assert result.summary.categories["COOKIE"] >= 1
