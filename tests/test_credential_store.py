import os
from coding_harness.credential_store import EnvCredentialStore, mask_key


def test_mask_key():
    assert mask_key("sk-ant-api03-abcdef123456") == "****3456"


def test_env_store_get_set_clear(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    store = EnvCredentialStore()
    assert store.get() is None
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-abcdef123456")
    assert store.get() == "sk-ant-api03-abcdef123456"
    assert "3456" in store.status() and "abcdef" not in store.status()
    store.clear()
    assert store.get() is None