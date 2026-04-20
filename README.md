# Log Analyzer for L2 RCA

Dark-themed local RCA tool for L2, Technical Support, SRE, and Incident Response workflows.

The project focuses on one job: paste mixed production-like logs and get a concise RCA-oriented result:

- detected log source formats;
- grouped failure patterns;
- dominant issue;
- rule-based classification;
- examples for each group;
- concrete L2 investigation actions.

The app is intentionally local-first and lightweight: **Python + FastAPI + static HTML/CSS/JS**, no Node.js build chain required.

## Why This Project Exists

During incidents, L2 engineers often receive log fragments from Kibana, Grafana Loki, container logs, SSH sessions, database logs, or application stack traces. The hard part is not only reading one line, but finding repeated failure patterns hidden behind dynamic values such as IP addresses, ports, request IDs, UUIDs, pod names, user IDs, and timestamps.

This project demonstrates:

- broad log parsing;
- multiline stack trace handling;
- dynamic value normalization;
- error deduplication;
- YAML-based RCA classification;
- practical recommended actions;
- FastAPI API design;
- automated tests.

## Supported Inputs

The analyzer accepts mixed logs in one paste:

- Elastic/Kibana-style JSON and ECS-like fields;
- Grafana Loki JSON and logfmt-style lines;
- Docker `json-file` logs;
- Kubernetes CRI/container runtime logs;
- Nginx and Apache access logs;
- Nginx error logs;
- syslog RFC3164/RFC5424-like lines;
- PostgreSQL error logs with `DETAIL` and `STATEMENT` continuation lines;
- MySQL error logs;
- Redis logs;
- Java/Spring logs and stack traces;
- Python logs and tracebacks;
- plain text fallback.

The sample corpus is here:

```text
samples/rca_mixed_test_logs.log
```

It is a safe synthetic corpus built around public log formats, not private production data.

## Project Structure

```text
backend/
  app/
    main.py
    models.py
    analyzer/
      parser.py
      normalizer.py
      deduplicator.py
      classifier.py
      insights.py
      engine.py
    rules/rules.yaml
  tests/
samples/
  rca_mixed_test_logs.log
web/
  index.html
  static/css/app.css
  static/js/app.js
README.md
README_RU.md
requirements.txt
pytest.ini
```

## Requirements

- Python 3.12+
- PowerShell, Windows Terminal, or another shell

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual environment activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Run the App

```powershell
python -m uvicorn backend.app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

The UI can also be opened directly from `web/index.html`, but the API still needs the backend running on `http://127.0.0.1:8000`.

## API

Health:

```http
GET /health
```

Analyze logs:

```http
POST /api/analyze
```

Request:

```json
{
  "text": "raw pasted logs",
  "source_type": "auto",
  "max_groups": 12
}
```

Response:

```json
{
  "summary": {
    "total_lines": 0,
    "parsed_lines": 0,
    "error_events": 0,
    "unique_patterns": 0,
    "dominant_issue": null,
    "dominant_percentage": 0,
    "source_types": {}
  },
  "groups": [],
  "insights": []
}
```

## How It Works

Pipeline:

```text
raw logs
  -> multiline record coalescing
  -> format parser
  -> dynamic value normalizer
  -> warning/error/fatal extractor
  -> deduplicator
  -> YAML classifier
  -> RCA insight generator
```

The normalizer replaces values that should not create separate groups:

- IPs and ports;
- URLs and hostnames;
- timestamps and dates;
- UUIDs and long hex IDs;
- request, trace, span, correlation, user, session, order, and client IDs;
- long numeric IDs;
- durations and sizes;
- stack trace frames.

## RCA Rules

Rules are stored in:

```text
backend/app/rules/rules.yaml
```

Current categories include:

- `GATEWAY_ERROR`
- `NETWORK_ERROR`
- `DNS_ERROR`
- `TIMEOUT`
- `RESOURCE_EXHAUSTION`
- `APPLICATION_ERROR`
- `DATABASE_ERROR`
- `KUBERNETES_ERROR`
- `AUTH_ERROR`
- `TLS_CERTIFICATE_ERROR`
- `RATE_LIMIT`
- `MESSAGE_BROKER_ERROR`
- `CACHE_ERROR`
- `UNKNOWN`

## Tests

Run:

```powershell
python -m pytest
```

Current tests cover:

- ECS-like JSON parsing;
- Loki/logfmt parsing;
- Docker JSON parsing;
- Kubernetes CRI parsing;
- Nginx/Apache access and Nginx error logs;
- PostgreSQL, MySQL, Redis, syslog, Java, Python parsing;
- multiline stack traces;
- normalization and grouping;
- YAML classification;
- API validation;
- sample corpus analysis.

## Reference Formats

The parser and sample corpus were shaped around public documentation for common log formats:

- Elastic ECS log fields: https://www.elastic.co/docs/reference/ecs/ecs-log
- Grafana Loki log queries and parsers: https://grafana.com/docs/loki/latest/query/log_queries/
- Docker `json-file` logging driver: https://docs.docker.com/engine/logging/drivers/json-file/
- Kubernetes logging architecture and CRI logging: https://kubernetes.io/docs/concepts/cluster-administration/logging/
- Apache HTTP Server log files: https://httpd.apache.org/docs/2.4/en/logs.html
- NGINX logging: https://docs.nginx.com/nginx/admin-guide/monitoring/logging/
- PostgreSQL error reporting and logging: https://www.postgresql.org/docs/current/runtime-config-logging.html
- MySQL error log format: https://dev.mysql.com/doc/refman/en/error-log-format.html

## Portfolio Positioning

Suggested interview description:

```text
I built a FastAPI-based L2 RCA analyzer that accepts mixed logs from modern observability and infrastructure sources, normalizes dynamic values, groups repeated failures, classifies issues through YAML rules, and returns concrete investigation actions.
```

## Next Iterations

- File upload for `.log`, `.txt`, and `.jsonl`.
- Timeline aggregation by minute.
- Incident summary export.
- User-editable RCA rules.
- Dockerfile and docker-compose.
- GitHub Actions for automated tests.
