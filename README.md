# L2 Incident Workbench

Local-first FastAPI tool for L2, Technical Support, SRE, and Incident Response workflows.

The workbench currently has two focused modes:

- `RCA Analyzer` for grouping failure patterns and generating root-cause hints from mixed logs.
- `Log Sanitizer` for detecting and masking sensitive data before logs are shared with vendors, AI tools, incident channels, or tickets.

The project stays intentionally lightweight: Python, FastAPI, and static HTML/CSS/JS with no Node.js build chain required.

## Why This Project Exists

During incidents, L2 engineers usually handle two painful tasks at the same time:

- understand repeated failure patterns hidden inside noisy logs;
- share log fragments safely without leaking secrets, PII, tokens, or internal infrastructure details.

This project targets both workflows in one local tool:

- broad log parsing;
- multiline stack trace handling;
- dynamic value normalization;
- error grouping and RCA classification;
- rule-based investigation hints;
- local log sanitization with correlation-preserving masking;
- automated backend tests.

## What The Workbench Does

### RCA Analyzer

Accepts mixed logs from a single paste:

- Elastic/Kibana JSON and ECS-like fields;
- Grafana Loki JSON and logfmt;
- Docker `json-file` logs;
- Kubernetes CRI/container runtime logs;
- Nginx and Apache access logs;
- Nginx error logs;
- syslog-like lines;
- PostgreSQL, MySQL, and Redis logs;
- Java/Spring logs and stack traces;
- Python logs and tracebacks;
- plain text fallback.

Returns:

- detected source formats;
- grouped failure patterns;
- dominant issue;
- RCA insights;
- recommended investigation actions.

### Log Sanitizer

Accepts pasted logs and produces a safe-to-share version.

Current built-in detections include:

- bearer tokens and authorization headers;
- JWT-like tokens;
- cookies;
- passwords and secret fields;
- API keys and access tokens;
- email addresses;
- phone numbers;
- IPv4 addresses;
- request, trace, span, session, correlation, user, and client IDs;
- URL fields;
- host and upstream fields;
- credit-card-like values validated with Luhn checks.

Supports:

- `mask` mode;
- `hash` mode;
- correlation-preserving masking in `mask` mode;
- examples of replacements;
- direct handoff of sanitized logs into the RCA Analyzer UI.

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
    sanitizer/
      builtins.py
      engine.py
    rules/rules.yaml
  tests/
samples/
  rca_mixed_test_logs.log
  sanitizer_sensitive_test_logs.log
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

## Run The App

```powershell
python -m uvicorn backend.app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Sample Files

- RCA sample corpus: `samples/rca_mixed_test_logs.log`
- sanitizer sample corpus: `samples/sanitizer_sensitive_test_logs.log`

Both corpora are synthetic and safe. They are based on public log format references, not private production data.

## API

Health:

```http
GET /health
```

RCA analysis:

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

Log sanitization:

```http
POST /api/sanitize
```

Request:

```json
{
  "text": "raw pasted logs",
  "mode": "mask",
  "preserve_correlation": true
}
```

Response:

```json
{
  "summary": {
    "total_lines": 0,
    "transformed_lines": 0,
    "total_matches": 0,
    "categories": {}
  },
  "sanitized_text": "",
  "examples": []
}
```

## How It Works

### RCA pipeline

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

### Sanitizer pipeline

```text
raw logs
  -> JSON-aware sanitization
  -> logfmt-aware sanitization
  -> regex-based detection for plain text
  -> optional correlation-preserving replacement
  -> replacement report + safe-to-share text
```

The sanitizer preserves JSON structure when possible and supports deterministic replacements inside one sanitization run, so the same sensitive value can stay traceable as `<EMAIL:1>`, `<REQUEST_ID:2>`, and similar placeholders.

## Tests

Run:

```powershell
python -m pytest
```

Current coverage includes:

- mixed log parsing across common real-world formats;
- multiline stack traces;
- normalization and grouping;
- YAML classification;
- sanitizer masking and hashing behavior;
- correlation-preserving replacements;
- JSON-safe sanitization;
- API validation for both `/api/analyze` and `/api/sanitize`.

## Reference Formats And Product Inspiration

Parser and sample corpora were shaped around public documentation for common log formats:

- Elastic ECS log fields: https://www.elastic.co/docs/reference/ecs/ecs-log
- Grafana Loki log queries and parsers: https://grafana.com/docs/loki/latest/query/log_queries/
- Docker `json-file` logging driver: https://docs.docker.com/engine/logging/drivers/json-file/
- Kubernetes logging architecture and CRI logging: https://kubernetes.io/docs/concepts/cluster-administration/logging/
- Apache HTTP Server log files: https://httpd.apache.org/docs/2.4/en/logs.html
- NGINX logging: https://docs.nginx.com/nginx/admin-guide/monitoring/logging/
- PostgreSQL logging: https://www.postgresql.org/docs/current/runtime-config-logging.html
- MySQL error log format: https://dev.mysql.com/doc/refman/en/error-log-format.html

Related commercial workflow categories:

- Datadog Sensitive Data Scanner: https://docs.datadoghq.com/security/sensitive_data_scanner/
- Splunk anonymize and field filters: https://help.splunk.com/en/splunk-enterprise/get-started/get-data-in/9.1/configure-event-processing/anonymize-data
- Cribl PII masking: https://docs.cribl.io/use-cases/usecase-pii/

## Portfolio Positioning

Suggested interview description:

```text
I built a local-first L2 incident workbench with two practical workflows: mixed-log RCA analysis and safe log sanitization for vendor support, AI tooling, and incident communication.
```

## Next Iterations

- file upload for `.log`, `.txt`, and `.jsonl`;
- export of sanitized reports and RCA summaries;
- timeline aggregation by minute;
- custom sanitizer rules from UI;
- incident report generation;
- GitHub Actions and UI smoke tests.
