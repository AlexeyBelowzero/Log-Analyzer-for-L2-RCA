# Log Analyzer for L2 RCA - инструкция на русском

Этот файл предназначен для личного использования. Публичный файл для портфолио остается `README.md` на английском языке.

## 1. Что это за проект сейчас

Проект сфокусирован только на одной сильной задаче - RCA Log Analyzer

Цель сервиса: принять смешанные логи из разных источников, сгруппировать повторяющиеся ошибки, определить доминирующую проблему и выдать понятные L2/RCA-подсказки.

Основная идея, которую я воплотил:

I built a FastAPI-based L2 RCA analyzer that accepts mixed logs from modern observability and infrastructure sources, normalizes dynamic values, groups repeated failures, classifies issues through YAML rules, and returns concrete investigation actions.


## 2. Что умеет сервис

Сервис умеет читать смешанный набор логов в одном поле:

- JSON / ECS-like logs из Kibana/Elastic;
- JSON и logfmt-like строки, которые часто встречаются в Grafana Loki;
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

Важно: это не значит, что сервис гарантированно идеально распарсит вообще любой кастомный лог в мире. Но он покрывает широкий набор реальных распространенных форматов и имеет fallback, чтобы не падать на неизвестных строках.

## 3. Структура проекта

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── analyzer/
│   │   │   ├── parser.py
│   │   │   ├── normalizer.py
│   │   │   ├── deduplicator.py
│   │   │   ├── classifier.py
│   │   │   ├── insights.py
│   │   │   └── engine.py
│   │   └── rules/
│   │       └── rules.yaml
│   └── tests/
├── samples/
│   └── rca_mixed_test_logs.log
├── web/
│   ├── index.html
│   └── static/
│       ├── css/app.css
│       └── js/app.js
├── README.md
├── README_RU.md
├── requirements.txt
└── pytest.ini
```

Назначение основных файлов:

- `backend/app/main.py` - FastAPI-приложение, endpoint `/api/analyze`, health check и раздача UI.
- `backend/app/models.py` - Pydantic-модели запросов и ответов.
- `backend/app/analyzer/parser.py` - распознавание форматов логов.
- `backend/app/analyzer/normalizer.py` - замена динамических значений на плейсхолдеры.
- `backend/app/analyzer/deduplicator.py` - группировка похожих ошибок.
- `backend/app/analyzer/classifier.py` - классификация групп по YAML-правилам.
- `backend/app/analyzer/insights.py` - генерация RCA-подсказок.
- `backend/app/analyzer/engine.py` - общий pipeline анализа.
- `backend/app/rules/rules.yaml` - правила RCA.
- `samples/rca_mixed_test_logs.log` - тестовый набор логов для ручной проверки.
- `web/index.html` - интерфейс.
- `web/static/css/app.css` - темная тема в стиле GitHub/VS Code.
- `web/static/js/app.js` - логика frontend.

## 4. Как запустить сервис

В проекте есть две части:

- **Backend** - Python/FastAPI-сервер. Он реально анализирует логи.
- **Frontend** - страница в браузере. Она отправляет логи на backend и показывает результат.

Главное правило: сначала запускается backend, потом открывается браузер.

### 4.1. Первый запуск после скачивания или после создания проекта

Эти шаги нужно выполнить один раз.

1. Открой PowerShell.

   Можно открыть обычный PowerShell или терминал внутри VS Code.

2. Перейди в папку проекта:

   ```powershell
   cd "C:\Users\user\Desktop\Projects\Log Analyzer for L2 RCA"
   ```

3. Создай виртуальное окружение `.venv`:

   ```powershell
   python -m venv .venv
   ```

   Что это значит: Python создаст отдельную папку `.venv`, куда будут установлены библиотеки только для этого проекта.

4. Активируй виртуальное окружение:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   Если все нормально, слева в PowerShell появится примерно такой префикс:

   ```text
   (.venv) PS C:\Users\user\Desktop\Projects\Log Analyzer for L2 RCA>
   ```

5. Если PowerShell пишет, что запуск скриптов запрещен, выполни:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

   Это разрешение действует только для текущего окна PowerShell.

6. Установи зависимости проекта:

   ```powershell
   python -m pip install -r requirements.txt
   ```

   Это установит FastAPI, Uvicorn, Pydantic, PyYAML, pytest и другие нужные библиотеки.

7. Запусти backend:

   ```powershell
   python -m uvicorn backend.app.main:app --reload
   ```

8. Если запуск успешный, в PowerShell появится примерно такой вывод:

   ```text
   INFO:     Started server process [...]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```

   Это значит: backend работает.

9. Не закрывай это окно PowerShell.

   Пока это окно открыто и сервер запущен, сайт может анализировать логи. Если закрыть PowerShell, backend остановится.

10. Открой браузер и перейди по адресу:

    ```text
    http://127.0.0.1:8000
    ```

### 4.2. Обычный запуск, если `.venv` уже создан

Это то, что нужно делать каждый раз, когда хочешь пользоваться сервисом.

1. Открой PowerShell.

2. Перейди в папку проекта:

   ```powershell
   cd "C:\Users\user\Desktop\Projects\Log Analyzer for L2 RCA"
   ```

3. Активируй виртуальное окружение:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. Запусти backend:

   ```powershell
   python -m uvicorn backend.app.main:app --reload
   ```

5. Дождись строки:

   ```text
   Uvicorn running on http://127.0.0.1:8000
   ```

6. Открой браузер:

   ```text
   http://127.0.0.1:8000
   ```

### 4.3. Как проверить, что backend работает

Открой второе окно PowerShell и выполни:

```powershell
curl http://127.0.0.1:8000/health
```

Ожидаемый ответ:

```json
{"status":"healthy"}
```

Если такой ответ есть, backend работает нормально.

### 4.4. Как остановить backend

Вернись в окно PowerShell, где запущен Uvicorn, и нажми:

```text
Ctrl + C
```

После этого сервер остановится, и сайт перестанет отправлять логи на анализ.

### 4.5. Частая ошибка

Если открыть просто файл:

```text
web/index.html
```

страница может открыться, но анализ будет работать только если backend отдельно запущен на:

```text
http://127.0.0.1:8000
```

Самый простой и правильный способ: запускать backend и открывать именно:

```text
http://127.0.0.1:8000
```

## 5. Как пользоваться после запуска

1. Убедись, что backend запущен и в PowerShell есть строка:

   ```text
   Uvicorn running on http://127.0.0.1:8000
   ```

2. Открой в браузере:

   ```text
   http://127.0.0.1:8000
   ```

3. Скопируй логи в поле `Paste logs`.

4. Нажми `Analyze logs`.

5. Смотри результат справа:

   - detected sources;
   - dominant issue;
   - grouped failure patterns;
   - RCA insights;
   - recommended actions.

Для проверки можно использовать файл:

```text
samples/rca_mixed_test_logs.log
```

Открой его, скопируй содержимое полностью и вставь в интерфейс.

## 5.1. Почему есть пустые `__init__.py`

Файлы `__init__.py` в Python используются для обозначения папки как Python package.

Примеры в проекте:

```text
backend/__init__.py
backend/app/__init__.py
backend/app/analyzer/__init__.py
```

Они могут быть пустыми. Это нормально.

Зачем они нужны:

- Python понимает, что папку можно импортировать как пакет.
- Импорты вида `from backend.app.analyzer.engine import LogAnalyzer` работают предсказуемо.
- Тесты и `uvicorn backend.app.main:app --reload` корректно находят модули проекта.

В современных версиях Python некоторые проекты могут работать и без `__init__.py` благодаря namespace packages, но для портфолио-проекта лучше оставить эти файлы: структура становится понятнее и стабильнее для запуска, тестов и IDE.

## 6. Что показывает результат

После анализа сервис показывает:

- `Total lines` - количество непустых строк во входном тексте.
- `Parsed records` - количество логических записей после склейки multiline stack traces.
- `Error events` - сколько записей признано warning/error/fatal/critical или похожими на ошибку.
- `Unique patterns` - количество уникальных нормализованных error patterns.
- `Dominant share` - доля самой частой ошибки.
- `Detected sources` - какие форматы логов были распознаны.
- `Dominant issue` - самая частая проблема.
- `Grouped failure patterns` - сгруппированные ошибки.
- `RCA insights` - возможные причины и действия.

Пример нормализации:

```text
Connection refused to upstream 10.42.1.15:8080 request_id=req-7001
Connection refused to upstream 10.42.1.16:8080 request_id=req-7002
```

Станет:

```text
Connection refused to upstream <IP>:<PORT> request_id=<ID>
```

Благодаря этому одинаковые ошибки не распадаются на разные группы из-за IP, портов и request_id.

## 7. Как работает pipeline

Общая цепочка:

```text
raw logs
  -> multiline record coalescing
  -> format parser
  -> dynamic value normalizer
  -> warning/error/fatal extractor
  -> deduplicator
  -> YAML classifier
  -> RCA insight generator
  -> API response
```

### 7.1. Multiline record coalescing

Файл:

```text
backend/app/analyzer/parser.py
```

Перед парсингом сервис склеивает continuation lines в одну запись.

Это нужно для Java/Python/PostgreSQL:

```text
2026-04-20 10:15:16,222 ERROR [payment-api] c.e.PaymentService - NullPointerException while placing bet
    at com.example.PaymentService.place(PaymentService.java:42)
    at com.example.PaymentController.handle(PaymentController.java:18)
Caused by: java.lang.IllegalStateException: missing odds
```

Такие строки считаются одной логической записью, а не четырьмя отдельными событиями.

### 7.2. Parser

Парсер пытается распознать формат в таком порядке:

- JSON;
- Docker JSON;
- Kubernetes CRI;
- Nginx error;
- Nginx/Apache access;
- syslog;
- PostgreSQL;
- MySQL;
- Redis;
- Spring;
- Java;
- Python;
- ISO timestamp + level;
- logfmt;
- plain text fallback.

Для JSON он ищет типичные поля:

- timestamp: `@timestamp`, `timestamp`, `time`, `ts`, `event.created`;
- level: `log.level`, `level`, `severity`, `severity_text`;
- service: `service.name`, `service`, `app`, `application`, `container.name`;
- message: `message`, `msg`, `error.message`, `event.original`, `log`.

### 7.3. Normalizer

Файл:

```text
backend/app/analyzer/normalizer.py
```

Normalizer заменяет динамические значения:

- URL -> `<URL>`;
- UUID -> `<UUID>`;
- IP:PORT -> `<IP>:<PORT>`;
- IP -> `<IP>`;
- hostnames -> `<HOST>`;
- timestamps -> `<TIMESTAMP>`;
- dates -> `<DATE>`;
- request_id / trace_id / span_id / correlation_id / user_id -> `<ID>`;
- длинные числовые ID -> `<NUMBER>`;
- durations -> `<DURATION>`;
- memory sizes -> `<SIZE>`;
- stack trace frames -> `<STACK_FRAME>` / `<PYTHON_FRAME>`.

### 7.4. Error extractor

В анализ попадают записи с уровнями:

- `WARNING`;
- `ERROR`;
- `FATAL`;
- `CRITICAL`.

Также plain text может попасть в анализ, если содержит слова вроде:

- error;
- exception;
- failed;
- timeout;
- refused;
- denied;
- OOMKilled;
- Bad Gateway;
- CrashLoopBackOff;
- deadlock;
- certificate;
- x509.

### 7.5. Deduplicator

Файл:

```text
backend/app/analyzer/deduplicator.py
```

Группирует записи по нормализованному сообщению.

Для каждой группы сохраняется:

- pattern;
- count;
- level;
- service;
- source_type;
- classification;
- examples.

### 7.6. Classifier и rules.yaml

Файл правил:

```text
backend/app/rules/rules.yaml
```

Каждое правило содержит:

- `name`;
- `pattern`;
- `classification`;
- `insight`;
- `possible_causes`;
- `actions`.

Категории сейчас:

- `GATEWAY_ERROR`;
- `NETWORK_ERROR`;
- `DNS_ERROR`;
- `TIMEOUT`;
- `RESOURCE_EXHAUSTION`;
- `APPLICATION_ERROR`;
- `DATABASE_ERROR`;
- `KUBERNETES_ERROR`;
- `AUTH_ERROR`;
- `TLS_CERTIFICATE_ERROR`;
- `RATE_LIMIT`;
- `MESSAGE_BROKER_ERROR`;
- `CACHE_ERROR`;
- `UNKNOWN`.

Пример:

```yaml
- name: Connection refused
  pattern: "connection refused|connect\\(\\) failed|connection reset|no route to host"
  classification: NETWORK_ERROR
  insight: Upstream connectivity failures detected
  possible_causes:
    - Upstream service is down or has no healthy endpoints
    - Wrong host or port in service configuration
  actions:
    - Check service health and endpoint readiness
    - Validate configured upstream host and port
```

## 8. API

### Health

```http
GET /health
```

Проверка:

```powershell
curl http://127.0.0.1:8000/health
```

Ответ:

```json
{"status":"healthy"}
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

## 9. Тесты

Запуск:

```powershell
python -m pytest
```

Что проверяется:

- ECS-like JSON;
- logfmt/Loki-style lines;
- Docker JSON;
- Kubernetes CRI;
- Nginx/Apache access;
- Nginx error;
- PostgreSQL;
- MySQL;
- Redis;
- syslog;
- Java logs;
- Python logs;
- multiline stack traces;
- normalization;
- grouping;
- classification;
- API validation;
- sample log corpus.

## 10. Тестовый файл логов

Файл:

```text
samples/rca_mixed_test_logs.log
```

Это безопасный synthetic corpus, собранный на основе публичных форматов из документации, а не реальные приватные production logs.

Он содержит:

- ECS JSON;
- logfmt;
- CRI;
- Docker JSON;
- Nginx/Apache access;
- Nginx error;
- PostgreSQL multiline;
- MySQL;
- Redis;
- Java stack trace;
- Python traceback;
- syslog/kubelet;
- auth error;
- TLS certificate error;
- rate limit;
- OOMKilled;
- normal info line.

## 11. Типовые проблемы

### Сайт открылся, но Analyze не работает

Backend не запущен.

```powershell
python -m uvicorn backend.app.main:app --reload
```

### Порт 8000 занят

Можно запустить на другом порту:

```powershell
python -m uvicorn backend.app.main:app --reload --port 8001
```

Но если открываешь `web/index.html` напрямую, JS ожидает API на:

```text
http://127.0.0.1:8000
```

Если используешь порт 8001, открывай UI через:

```text
http://127.0.0.1:8001
```

### Тесты не запускаются

Установи зависимости:

```powershell
python -m pip install -r requirements.txt
```

Потом:

```powershell
python -m pytest
```

## 12. Что улучшать дальше

Приоритеты:

1. File upload для `.log`, `.txt`, `.jsonl`.
2. Timeline aggregation по минутам.
3. Incident report export.
4. UI для редактирования `rules.yaml`.
5. Dockerfile и docker-compose.
6. GitHub Actions.
7. Playwright smoke tests.
8. Поддержка CloudWatch Logs, OpenSearch JSON DSL, journald export.

## 13. Источники форматов

При рефакторинге использовались публичные описания форматов:

- Elastic ECS log fields: https://www.elastic.co/docs/reference/ecs/ecs-log
- Grafana Loki log queries and parsers: https://grafana.com/docs/loki/latest/query/log_queries/
- Docker `json-file` logging driver: https://docs.docker.com/engine/logging/drivers/json-file/
- Kubernetes logging architecture and CRI logging: https://kubernetes.io/docs/concepts/cluster-administration/logging/
- Apache HTTP Server log files: https://httpd.apache.org/docs/2.4/en/logs.html
- NGINX logging: https://docs.nginx.com/nginx/admin-guide/monitoring/logging/
- PostgreSQL error reporting and logging: https://www.postgresql.org/docs/current/runtime-config-logging.html
- MySQL error log format: https://dev.mysql.com/doc/refman/en/error-log-format.html
