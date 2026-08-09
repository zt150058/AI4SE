import os
from abc import ABC, abstractmethod

ENV_VAR = "ANTHROPIC_API_KEY"

def mask_key(key: str | None) -> str:
    if not key:
        return "<not set>"
    return "****" + key[-4:] if len(key) >= 4 else "****"

class CredentialPort(ABC):
    @abstractmethod
    def get(self) -> str | None: ...
    @abstractmethod
    def set(self, key: str) -> None: ...
    @abstractmethod
    def clear(self) -> None: ...
    def status(self) -> str:
        return mask_key(self.get())

class EnvCredentialStore(CredentialPort):
    def get(self) -> str | None:
        return os.environ.get(ENV_VAR)
    def set(self, key: str) -> None:
        os.environ[ENV_VAR] = key
    def clear(self) -> None:
        os.environ.pop(ENV_VAR, None)

class KeyringCredentialStore(CredentialPort):
    SERVICE = "coding-harness"
    def __init__(self) -> None:
        import keyring  # lazy import; not used in tests
        self._kr = keyring
    def get(self) -> str | None:
        return self._kr.get_password(self.SERVICE, "api_key")
    def set(self, key: str) -> None:
        self._kr.set_password(self.SERVICE, "api_key", key)
    def clear(self) -> None:
        try:
            self._kr.delete_password(self.SERVICE, "api_key")
        except Exception:
            pass