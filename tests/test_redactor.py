# tests/test_redactor.py
from coding_harness.redactor import redact

def test_scrubs_anthropic_key():
    s = "error: key=sk-ant-api03-abcdef123456 called"
    out = redact(s)
    assert "sk-ant-api03-abcdef123456" not in out
    assert "sk-ant-" in out or "REDACTED" in out

def test_leaves_plain_text():
    assert redact("no secrets here") == "no secrets here"

def test_scrubs_multiple():
    s = "a=sk-ant-xxx b=sk-ant-yyy"
    out = redact(s)
    assert "xxx" not in out and "yyy" not in out
