"""Privacy guardrails — redact secrets / PII before persistence or display."""

from __future__ import annotations

import re

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("api_key", re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{16,})")),
    ("bearer", re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("phone_cn", re.compile(r"\b1[3-9]\d{9}\b")),
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]


def redact_text(text: str) -> tuple[str, list[str]]:
    """Return redacted text and list of hit pattern names."""
    hits: list[str] = []
    out = text
    for name, pat in _PATTERNS:
        if pat.search(out):
            hits.append(name)
            if name == "api_key":
                out = pat.sub(r"\1=[REDACTED]", out)
            else:
                out = pat.sub("[REDACTED]", out)
    return out, hits


def is_exfiltration_request(query: str) -> bool:
    q = query.lower()
    needles = [
        "发到微信",
        "上传到chatgpt",
        "发到公网",
        "paste to public",
        "send to gmail",
        "发给外部",
    ]
    return any(n in q for n in needles)


def privacy_block_message() -> str:
    return (
        "隐私护栏已拦截：该请求疑似将敏感内容外发到公网/外部聊天工具。"
        "请仅在 PrivateLocalAgent / 批准的本地模型内处理涉密数据。"
    )
