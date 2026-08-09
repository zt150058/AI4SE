# src/coding_harness/redactor.py
import re

SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]+"),
]
_REPLACEMENT = "sk-ant-***REDACTED***"

def redact(text: str) -> str:
    out = text
    for pat in SECRET_PATTERNS:
        out = pat.sub(_REPLACEMENT, out)
    return out
