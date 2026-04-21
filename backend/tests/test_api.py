from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_analyze_endpoint_returns_dominant_connection_refused() -> None:
    logs = "\n".join(
        [
            '{"@timestamp":"2026-04-20T10:15:01Z","level":"ERROR","service":"bettingservice","message":"Connection refused to upstream 10.1.2.3:8080"}',
            '{"@timestamp":"2026-04-20T10:15:02Z","level":"ERROR","service":"bettingservice","message":"Connection refused to upstream 10.1.2.4:8080"}',
            '{"@timestamp":"2026-04-20T10:15:05Z","level":"ERROR","service":"bettingservice","message":"Read timeout on endpoint /api/bet/place"}',
        ]
    )

    response = client.post("/api/analyze", json={"text": logs, "source_type": "auto", "max_groups": 10})
    payload = response.json()

    assert response.status_code == 200
    assert payload["summary"]["error_events"] == 3
    assert payload["summary"]["unique_patterns"] == 2
    assert payload["summary"]["dominant_issue"] == "Connection refused to upstream <IP>:<PORT>"
    assert payload["summary"]["source_types"] == {"json": 3}
    assert payload["groups"][0]["classification"] == "NETWORK_ERROR"
    assert payload["insights"][0]["classification"] == "NETWORK_ERROR"


def test_analyze_endpoint_rejects_empty_input() -> None:
    response = client.post("/api/analyze", json={"text": "   "})

    assert response.status_code == 422


def test_sanitize_endpoint_returns_masked_output() -> None:
    logs = '{"user_email":"alex@example.com","request_id":"req-123","authorization":"Bearer abc.def.ghi"}'

    response = client.post(
        "/api/sanitize",
        json={"text": logs, "mode": "mask", "preserve_correlation": True},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["summary"]["total_matches"] >= 3
    assert "alex@example.com" not in payload["sanitized_text"]
    assert payload["examples"]


def test_sanitize_endpoint_rejects_empty_input() -> None:
    response = client.post("/api/sanitize", json={"text": "  "})

    assert response.status_code == 422


def test_query_assistant_endpoint_was_removed() -> None:
    response = client.post("/api/queries", json={})

    assert response.status_code == 404
