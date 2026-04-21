# L2 Incident Workbench - инструкция на русском

Этот файл предназначен для личного использования. Публичный файл для портфолио остается `README.md` на английском языке.

## 1. Что это за проект сейчас

Проект больше не ограничивается только RCA-анализом. Теперь это локальный `L2 Incident Workbench` с двумя практическими режимами:

- `RCA Analyzer`
- `Log Sanitizer`

То есть сервис закрывает две реальные L2-задачи:

1. понять, что ломается в логах и какая проблема доминирует;
2. безопасно очистить логи перед отправкой во внешний чат, тикет, vendor support или AI-инструмент.

Идея, которую можно использовать на собеседовании:

```text
I built a local-first L2 incident workbench with two practical workflows: mixed-log RCA analysis and safe log sanitization for vendor support, AI tooling, and incident communication.
```

## 2. Что умеет сервис

### 2.1. RCA Analyzer

Принимает смешанные логи и:

- распознает source formats;
- группирует одинаковые ошибки;
- показывает dominant issue;
- классифицирует проблемы по YAML rules;
- выдает RCA hints и recommended actions.

Поддерживаемые форматы:

- JSON / ECS-like logs из Kibana/Elastic;
- JSON и logfmt-like строки из Grafana Loki;
- Docker `json-file` logs;
- Kubernetes CRI/container runtime logs;
- Nginx/Apache access logs;
- Nginx error logs;
- syslog-like logs;
- PostgreSQL error logs;
- MySQL error logs;
- Redis logs;
- Java/Spring logs и stack traces;
- Python logs и tracebacks;
- plain text fallback.

### 2.2. Log Sanitizer

Принимает логи и строит безопасную для пересылки версию.

Сейчас санитайзер умеет искать и заменять:

- bearer tokens и authorization headers;
- JWT;
- cookies;
- password / secret fields;
- API keys и access tokens;
- email;
- phone;
- IPv4;
- request_id / trace_id / span_id / session_id / correlation_id / user_id / client_id;
- URL fields;
- host/upstream fields;
- credit-card-like значения.

Поддерживаются режимы:

- `mask`
- `hash`
- preserve correlation в `mask` mode

Пример:

```text
user_email=alex@example.com
request_id=req-1001
user_email=alex@example.com
```

После sanitize:

```text
user_email=<EMAIL:1>
request_id=<REQUEST_ID:1>
user_email=<EMAIL:1>
```

Это полезно, потому что реальные значения скрыты, но корреляция внутри одного массива логов сохраняется.

## 3. Структура проекта

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

Основные файлы:

- `backend/app/main.py` - FastAPI app, endpoints `/api/analyze` и `/api/sanitize`, health check, раздача UI.
- `backend/app/models.py` - Pydantic-модели запросов и ответов.
- `backend/app/analyzer/` - логика RCA analysis.
- `backend/app/sanitizer/` - логика log sanitization.
- `backend/app/rules/rules.yaml` - правила классификации RCA.
- `samples/rca_mixed_test_logs.log` - тестовый набор для RCA Analyzer.
- `samples/sanitizer_sensitive_test_logs.log` - тестовый набор для Log Sanitizer.
- `web/index.html` - интерфейс с двумя режимами.
- `web/static/css/app.css` - темная тема.
- `web/static/js/app.js` - логика frontend.

## 4. Как запустить сервис

В проекте есть две части:

- `Backend` - Python/FastAPI-сервер, который реально обрабатывает данные.
- `Frontend` - страница в браузере, которая отправляет данные в backend и показывает результат.

Главное правило: сначала запускается backend, потом открывается браузер.

### 4.1. Первый запуск

1. Открой PowerShell.

2. Перейди в папку проекта:

   ```powershell
   cd "C:\Users\user\Desktop\Projects\Log Analyzer for L2 RCA"
   ```

3. Создай виртуальное окружение:

   ```powershell
   python -m venv .venv
   ```

4. Активируй его:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

5. Если PowerShell запрещает запуск скриптов:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

6. Установи зависимости:

   ```powershell
   python -m pip install -r requirements.txt
   ```

7. Запусти backend:

   ```powershell
   python -m uvicorn backend.app.main:app --reload
   ```

8. Дождись строки:

   ```text
   Uvicorn running on http://127.0.0.1:8000
   ```

9. Открой в браузере:

   ```text
   http://127.0.0.1:8000
   ```

### 4.2. Обычный запуск

Если `.venv` уже создан и зависимости установлены:

```powershell
cd "C:\Users\user\Desktop\Projects\Log Analyzer for L2 RCA"
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --reload
```

Потом открыть:

```text
http://127.0.0.1:8000
```

### 4.3. Как проверить, что backend работает

Открой второе окно PowerShell:

```powershell
curl http://127.0.0.1:8000/health
```

Ожидаемый ответ:

```json
{"status":"healthy"}
```

### 4.4. Как остановить backend

В окне PowerShell, где запущен Uvicorn:

```text
Ctrl + C
```

## 5. Как пользоваться после запуска

### 5.1. RCA Analyzer

1. Убедись, что backend запущен.
2. Открой `http://127.0.0.1:8000`.
3. На вкладке `RCA Analyzer` вставь логи в поле `Paste logs`.
4. Нажми `Analyze logs`.
5. Смотри результат справа:
   - detected sources;
   - dominant issue;
   - grouped failure patterns;
   - RCA insights;
   - recommended actions.

Для ручной проверки можно использовать:

```text
samples/rca_mixed_test_logs.log
```

### 5.2. Log Sanitizer

1. Перейди на вкладку `Log Sanitizer`.
2. Вставь логи в поле `Paste logs to sanitize`.
3. Выбери режим:
   - `mask` - скрывает значения как `<EMAIL>`, `<IP>`, `<REQUEST_ID>`;
   - `hash` - скрывает значения через короткий hash-like placeholder.
4. Включи или выключи `Preserve correlation in mask mode`.
5. Нажми `Sanitize logs`.
6. Смотри результат:
   - summary;
   - detected categories;
   - replacement examples;
   - sanitized logs.

Дополнительно:

- кнопка `Copy` копирует sanitized output;
- кнопка `Use in analyzer` переносит очищенные логи в RCA Analyzer.

Для ручной проверки можно использовать:

```text
samples/sanitizer_sensitive_test_logs.log
```

## 6. Почему есть пустые `__init__.py`

Файлы `__init__.py` в Python обозначают папку как пакет.

Они могут быть пустыми. Это нормально.

Зачем они нужны:

- Python корректно понимает imports;
- `uvicorn backend.app.main:app --reload` находит модули;
- тесты и IDE работают стабильнее.

## 7. Что показывает RCA Analyzer

После анализа сервис показывает:

- `Total lines`
- `Parsed records`
- `Error events`
- `Unique patterns`
- `Dominant share`
- `Detected sources`
- `Dominant issue`
- `Grouped failure patterns`
- `RCA insights`

## 8. Как устроен backend

### 8.1. RCA pipeline

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

### 8.2. Sanitizer pipeline

```text
raw logs
  -> JSON-aware sanitization
  -> logfmt-aware sanitization
  -> regex detection for plain text
  -> replacement policy
  -> sanitized output + summary + examples
```

Sanitizer старается не ломать structured logs:

- JSON старается оставить валидным JSON;
- logfmt обрабатывает key=value;
- plain text проходит через regex rules.

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

## 10. Тесты

Запуск:

```powershell
python -m pytest
```

Что сейчас покрыто:

- mixed log parsing;
- multiline stack traces;
- normalization и grouping;
- YAML classification;
- sanitizer masking;
- sanitizer hash mode;
- correlation-preserving replacements;
- JSON-safe sanitization;
- API `/api/analyze`;
- API `/api/sanitize`.

## 11. Тестовые файлы

RCA:

```text
samples/rca_mixed_test_logs.log
```

Sanitizer:

```text
samples/sanitizer_sensitive_test_logs.log
```

Оба файла synthetic и безопасны. Это не реальные production logs.

## 12. Типовые проблемы

### Сайт открылся, но ничего не анализирует и не санитайзит

Backend не запущен.

Запусти:

```powershell
python -m uvicorn backend.app.main:app --reload
```

### PowerShell не активирует `.venv`

Используй:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Порт 8000 занят

Можно временно запустить на другом порту:

```powershell
python -m uvicorn backend.app.main:app --reload --port 8001
```

И открыть:

```text
http://127.0.0.1:8001
```

## 13. Что развивать дальше

Самые логичные следующие шаги:

1. file upload;
2. incident summary export;
3. custom sanitizer rules from UI;
4. runbook copilot;
5. timeline aggregation;
6. incident report generation;
7. GitHub Actions;
8. Playwright smoke tests.

## 14. Источники форматов и идей

Публичные источники форматов:

- Elastic ECS log fields: https://www.elastic.co/docs/reference/ecs/ecs-log
- Grafana Loki log queries and parsers: https://grafana.com/docs/loki/latest/query/log_queries/
- Docker `json-file` logging driver: https://docs.docker.com/engine/logging/drivers/json-file/
- Kubernetes logging architecture and CRI logging: https://kubernetes.io/docs/concepts/cluster-administration/logging/
- Apache HTTP Server log files: https://httpd.apache.org/docs/2.4/en/logs.html
- NGINX logging: https://docs.nginx.com/nginx/admin-guide/monitoring/logging/
- PostgreSQL logging: https://www.postgresql.org/docs/current/runtime-config-logging.html
- MySQL error log format: https://dev.mysql.com/doc/refman/en/error-log-format.html

Продукты из похожей зоны:

- Datadog Sensitive Data Scanner: https://docs.datadoghq.com/security/sensitive_data_scanner/
- Splunk anonymize and field filters: https://help.splunk.com/en/splunk-enterprise/get-started/get-data-in/9.1/configure-event-processing/anonymize-data
- Cribl PII masking: https://docs.cribl.io/use-cases/usecase-pii/
