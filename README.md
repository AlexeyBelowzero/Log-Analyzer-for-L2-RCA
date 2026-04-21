# L2 Incident Workbench

This repository contains a local-first incident helper for L2 Support, Technical Support, SRE, and Incident Response workflows.

The public portfolio version is intentionally lightweight:

- backend: `Python 3.12 + FastAPI`
- frontend: static `HTML + CSS + JavaScript`
- runtime: no Node.js build chain required

## 1. What This Project Is

This project is no longer only an RCA analyzer. It is now a local `L2 Incident Workbench` with two practical modes:

- `RCA Analyzer`
- `Log Sanitizer`

In other words, the service helps with two real L2 tasks:

1. understand what is breaking in the logs and which issue is dominant;
2. safely clean logs before sending them to vendor support, an external chat, a ticket, or an AI tool.

Interview-ready description:

```text
I built a local-first L2 incident workbench with two practical workflows: mixed-log RCA analysis and safe log sanitization for vendor support, AI tooling, and incident communication.
```

## 2. What The Service Does

### 2.1. RCA Analyzer

The analyzer accepts mixed logs and:

- detects source formats;
- groups similar failures;
- shows the dominant issue;
- classifies problems with YAML rules;
- generates RCA hints and recommended actions.

Supported formats:

- JSON / ECS-like logs from Kibana and Elastic;
- JSON and logfmt-like lines from Grafana Loki;
- Docker `json-file` logs;
- Kubernetes CRI / container runtime logs;
- Nginx and Apache access logs;
- Nginx error logs;
- syslog-like logs;
- PostgreSQL error logs;
- MySQL error logs;
- Redis logs;
- Java / Spring logs and stack traces;
- Python logs and tracebacks;
- plain text fallback.

### 2.2. Log Sanitizer

The sanitizer accepts logs and creates a safe-to-share version.

Right now it can detect and replace:

- bearer tokens and authorization headers;
- JWTs;
- cookies;
- password / secret fields;
- API keys and access tokens;
- email addresses;
- phone numbers;
- IPv4 addresses;
- `request_id` / `trace_id` / `span_id` / `session_id` / `correlation_id` / `user_id` / `client_id`;
- URL fields;
- host / upstream fields;
- credit-card-like values.

Supported modes:

- `mask`
- `hash`
- preserve correlation in `mask` mode

Example:

```text
user_email=alex@example.com
request_id=req-1001
user_email=alex@example.com
```

After sanitization:

```text
user_email=<EMAIL:1>
request_id=<REQUEST_ID:1>
user_email=<EMAIL:1>
```

This is useful because the real values are hidden, but the correlation inside one log batch is preserved.

## 3. Project Structure

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

Main files:

- `backend/app/main.py` - FastAPI app, `/api/analyze` and `/api/sanitize`, health check, and UI serving.
- `backend/app/models.py` - Pydantic request and response models.
- `backend/app/analyzer/` - RCA analysis logic.
- `backend/app/sanitizer/` - log sanitization logic.
- `backend/app/rules/rules.yaml` - RCA classification rules.
- `samples/rca_mixed_test_logs.log` - test sample for the RCA Analyzer.
- `samples/sanitizer_sensitive_test_logs.log` - test sample for the Log Sanitizer.
- `web/index.html` - UI with two modes.
- `web/static/css/app.css` - dark theme styling.
- `web/static/js/app.js` - frontend logic.

## 4. How To Run The Service

There are two parts in this project:

- `Backend` - the Python / FastAPI server that actually processes data.
- `Frontend` - the page in the browser that sends requests to the backend and shows the result.

Main rule: start the backend first, then open the browser.

### 4.1. First Run

1. Clone the repository:

   ```powershell
   git clone https://github.com/AlexeyBelowzero/Log-Analyzer-for-L2-RCA.git
   ```

2. Open PowerShell.

3. Go to the project folder:

   ```powershell
   cd Log-Analyzer-for-L2-RCA
   ```

4. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

5. Activate it:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

6. If PowerShell blocks script execution:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

7. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

8. Start the backend:

   ```powershell
   python -m uvicorn backend.app.main:app --reload
   ```

9. Wait until you see:

   ```text
   Uvicorn running on http://127.0.0.1:8000
   ```

10. Open in the browser:

   ```text
   http://127.0.0.1:8000
   ```

### 4.2. Regular Run

If `.venv` already exists and dependencies are installed:

```powershell
cd Log-Analyzer-for-L2-RCA
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

### 4.3. How To Check That The Backend Is Working

Open a second PowerShell window:

```powershell
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"healthy"}
```

### 4.4. How To Stop The Backend

In the PowerShell window where Uvicorn is running:

```text
Ctrl + C
```

## 5. How To Use The App

### 5.1. RCA Analyzer

1. Make sure the backend is running.
2. Open `http://127.0.0.1:8000`.
3. On the `RCA Analyzer` tab, paste logs into the `Paste logs` field.
4. Click `Analyze logs`.
5. Review the result on the right:
   - detected sources;
   - dominant issue;
   - grouped failure patterns;
   - RCA insights;
   - recommended actions.

For manual testing, you can use:

```text
samples/rca_mixed_test_logs.log
```

### 5.2. Log Sanitizer

1. Open the `Log Sanitizer` tab.
2. Paste logs into the `Paste logs to sanitize` field.
3. Select a mode:
   - `mask` - hides values as placeholders like `<EMAIL>`, `<IP_ADDRESS>`, `<REQUEST_ID>`;
   - `hash` - hides values using a short hash-like placeholder.
4. Enable or disable `Preserve correlation in mask mode`.
5. Click `Sanitize logs`.
6. Review the result:
   - summary;
   - detected categories;
   - replacement examples;
   - sanitized logs.

Extra actions:

- `Copy` copies the sanitized output.
- `Use in analyzer` sends sanitized logs directly into the RCA Analyzer.

For manual testing, you can use:

```text
samples/sanitizer_sensitive_test_logs.log
```

## 6. Why Some `__init__.py` Files Are Empty

`__init__.py` files mark a directory as a Python package.

They can be empty. That is normal.

Why they are needed:

- Python handles imports correctly;
- `uvicorn backend.app.main:app --reload` can resolve modules;
- tests and IDE tooling behave more consistently.

## 7. What The RCA Analyzer Shows

After analysis, the service shows:

- `Total lines`
- `Parsed records`
- `Error events`
- `Unique patterns`
- `Dominant share`
- `Detected sources`
- `Dominant issue`
- `Grouped failure patterns`
- `RCA insights`

## 8. Backend Logic

### 8.1. RCA Pipeline

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

### 8.2. Sanitizer Pipeline

```text
raw logs
  -> JSON-aware sanitization
  -> logfmt-aware sanitization
  -> regex detection for plain text
  -> replacement policy
  -> sanitized output + summary + examples
```

The sanitizer tries not to break structured logs:

- JSON is kept valid whenever possible;
- logfmt is processed as `key=value`;
- plain text goes through regex rules.

## 9. API

### Health

```http
GET /health
```

### Analyze

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

### Sanitize

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

## 10. Tests

Run:

```powershell
python -m pytest
```

Current coverage includes:

- mixed log parsing;
- multiline stack traces;
- normalization and grouping;
- YAML classification;
- sanitizer masking;
- sanitizer hash mode;
- correlation-preserving replacements;
- JSON-safe sanitization;
- API `/api/analyze`;
- API `/api/sanitize`.

## 11. Test Files

RCA:

```text
samples/rca_mixed_test_logs.log
```

Sanitizer:

```text
samples/sanitizer_sensitive_test_logs.log
```

Both files are synthetic and safe. They are not real production logs.

## 12. Common Problems

### The UI opens, but nothing is analyzed or sanitized

The backend is not running.

Start it with:

```powershell
python -m uvicorn backend.app.main:app --reload
```

### PowerShell does not activate `.venv`

Use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Port 8000 is already in use

You can temporarily run the app on another port:

```powershell
python -m uvicorn backend.app.main:app --reload --port 8001
```

Then open:

```text
http://127.0.0.1:8001
```

## 13. What To Build Next

The most logical next steps are:

1. file upload;
2. incident summary export;
3. custom sanitizer rules from the UI;
4. runbook copilot;
5. timeline aggregation;
6. incident report generation;
7. GitHub Actions;
8. Playwright smoke tests.

## 14. Format References And Product Inspiration

Public references for formats:

- Elastic ECS log fields: https://www.elastic.co/docs/reference/ecs/ecs-log
- Grafana Loki log queries and parsers: https://grafana.com/docs/loki/latest/query/log_queries/
- Docker `json-file` logging driver: https://docs.docker.com/engine/logging/drivers/json-file/
- Kubernetes logging architecture and CRI logging: https://kubernetes.io/docs/concepts/cluster-administration/logging/
- Apache HTTP Server log files: https://httpd.apache.org/docs/2.4/en/logs.html
- NGINX logging: https://docs.nginx.com/nginx/admin-guide/monitoring/logging/
- PostgreSQL logging: https://www.postgresql.org/docs/current/runtime-config-logging.html
- MySQL error log format: https://dev.mysql.com/doc/refman/en/error-log-format.html

Products in a similar space:

- Datadog Sensitive Data Scanner: https://docs.datadoghq.com/security/sensitive_data_scanner/
- Splunk anonymize and field filters: https://help.splunk.com/en/splunk-enterprise/get-started/get-data-in/9.1/configure-event-processing/anonymize-data
- Cribl PII masking: https://docs.cribl.io/use-cases/usecase-pii/
