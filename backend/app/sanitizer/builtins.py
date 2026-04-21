from __future__ import annotations

import re
from dataclasses import dataclass


LOGFMT_RE = re.compile(r"(?P<key>[A-Za-z_][\w.\-]*)=(?P<value>\"[^\"]*\"|'[^']*'|[^\s]+)")

FIELD_CATEGORY_HINTS = {
    "email": "EMAIL",
    "user_email": "EMAIL",
    "mail": "EMAIL",
    "phone": "PHONE",
    "mobile": "PHONE",
    "ip": "IP_ADDRESS",
    "client_ip": "IP_ADDRESS",
    "remote_addr": "IP_ADDRESS",
    "forwarded_for": "IP_ADDRESS",
    "authorization": "BEARER_TOKEN",
    "auth": "BEARER_TOKEN",
    "cookie": "COOKIE",
    "set_cookie": "COOKIE",
    "password": "PASSWORD",
    "passwd": "PASSWORD",
    "pwd": "PASSWORD",
    "secret": "PASSWORD",
    "api_key": "API_KEY",
    "apikey": "API_KEY",
    "token": "API_KEY",
    "access_token": "API_KEY",
    "refresh_token": "API_KEY",
    "jwt": "JWT",
    "request_id": "REQUEST_ID",
    "req_id": "REQUEST_ID",
    "trace_id": "TRACE_ID",
    "span_id": "SPAN_ID",
    "session_id": "SESSION_ID",
    "correlation_id": "CORRELATION_ID",
    "user_id": "USER_ID",
    "client_id": "CLIENT_ID",
    "order_id": "ORDER_ID",
    "bet_id": "BET_ID",
    "card": "CREDIT_CARD",
    "card_number": "CREDIT_CARD",
    "pan": "CREDIT_CARD",
    "url": "URL",
    "uri": "URL",
    "endpoint": "URL",
    "host": "HOSTNAME",
    "hostname": "HOSTNAME",
    "server": "HOSTNAME",
    "upstream": "HOSTNAME",
}


@dataclass(frozen=True)
class RegexRule:
    category: str
    pattern: re.Pattern[str]
    value_group: str | None = None


REGEX_RULES = (
    RegexRule(
        category="BEARER_TOKEN",
        pattern=re.compile(r"(?P<prefix>\bBearer\s+)(?P<value>[A-Za-z0-9._~+/=-]+)", re.IGNORECASE),
        value_group="value",
    ),
    RegexRule(
        category="AUTH_HEADER",
        pattern=re.compile(r"(?P<prefix>\bAuthorization:\s*(?:Basic|Token)\s+)(?P<value>[^\s]+)", re.IGNORECASE),
        value_group="value",
    ),
    RegexRule(
        category="COOKIE",
        pattern=re.compile(r"(?P<prefix>\b(?:Cookie|Set-Cookie):\s*)(?P<value>[^\r\n]+)", re.IGNORECASE),
        value_group="value",
    ),
    RegexRule(
        category="PASSWORD",
        pattern=re.compile(
            r"(?P<prefix>\b(?:password|passwd|pwd|secret|client_secret)\s*[:=]\s*[\"']?)(?P<value>[^\"'\s,;]+)",
            re.IGNORECASE,
        ),
        value_group="value",
    ),
    RegexRule(
        category="API_KEY",
        pattern=re.compile(
            r"(?P<prefix>\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|token)\s*[:=]\s*[\"']?)(?P<value>[^\"'\s,;]+)",
            re.IGNORECASE,
        ),
        value_group="value",
    ),
    RegexRule(
        category="JWT",
        pattern=re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+\b"),
    ),
    RegexRule(
        category="EMAIL",
        pattern=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ),
    RegexRule(
        category="PHONE",
        pattern=re.compile(
            r"(?P<prefix>\b(?:phone|mobile|msisdn)\s*[:=]\s*)(?P<value>\+?\d[\d()\-\s]{7,}\d)",
            re.IGNORECASE,
        ),
        value_group="value",
    ),
    RegexRule(
        category="AWS_ACCESS_KEY",
        pattern=re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    RegexRule(
        category="REQUEST_ID",
        pattern=re.compile(
            r"(?P<prefix>\b(?:request|req)[_-]?id\s*[:=]\s*[\"']?)(?P<value>[A-Za-z0-9._:-]+)(?P<suffix>[\"']?)",
            re.IGNORECASE,
        ),
        value_group="value",
    ),
    RegexRule(
        category="REQUEST_ID",
        pattern=re.compile(r"\breq-[A-Za-z0-9._:-]+\b", re.IGNORECASE),
    ),
    RegexRule(
        category="TRACE_ID",
        pattern=re.compile(
            r"(?P<prefix>\btrace[_-]?id\s*[:=]\s*[\"']?)(?P<value>[A-Za-z0-9._:-]+)(?P<suffix>[\"']?)",
            re.IGNORECASE,
        ),
        value_group="value",
    ),
    RegexRule(
        category="SPAN_ID",
        pattern=re.compile(
            r"(?P<prefix>\bspan[_-]?id\s*[:=]\s*[\"']?)(?P<value>[A-Za-z0-9._:-]+)(?P<suffix>[\"']?)",
            re.IGNORECASE,
        ),
        value_group="value",
    ),
    RegexRule(
        category="CORRELATION_ID",
        pattern=re.compile(
            r"(?P<prefix>\bcorrelation[_-]?id\s*[:=]\s*[\"']?)(?P<value>[A-Za-z0-9._:-]+)(?P<suffix>[\"']?)",
            re.IGNORECASE,
        ),
        value_group="value",
    ),
    RegexRule(
        category="SESSION_ID",
        pattern=re.compile(
            r"(?P<prefix>\bsession[_-]?id\s*[:=]\s*[\"']?)(?P<value>[A-Za-z0-9._:-]+)(?P<suffix>[\"']?)",
            re.IGNORECASE,
        ),
        value_group="value",
    ),
    RegexRule(
        category="USER_ID",
        pattern=re.compile(
            r"(?P<prefix>\buser[_-]?id\s*[:=]\s*[\"']?)(?P<value>[A-Za-z0-9._:-]+)(?P<suffix>[\"']?)",
            re.IGNORECASE,
        ),
        value_group="value",
    ),
    RegexRule(
        category="CLIENT_ID",
        pattern=re.compile(
            r"(?P<prefix>\bclient[_-]?id\s*[:=]\s*[\"']?)(?P<value>[A-Za-z0-9._:-]+)(?P<suffix>[\"']?)",
            re.IGNORECASE,
        ),
        value_group="value",
    ),
    RegexRule(
        category="IP_ADDRESS",
        pattern=re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    ),
    RegexRule(
        category="URL",
        pattern=re.compile(r"\bhttps?://[^\s\"']+\b", re.IGNORECASE),
    ),
)
