"""凭据安全存储：端口 + 环境变量实现。

ANTHROPIC_API_KEY 仅以环境变量注入（EnvCredentialStore）或可选地落入 keyring
后端（KeyringCredentialStore，本项目未启用）。status()/mask_key() 仅返回掩码
形式 ****<last4>，绝不暴露明文。
"""
import os
from abc import ABC, abstractmethod

ENV_VAR = "ANTHROPIC_API_KEY"

def mask_key(key: str | None) -> str:
    """将密钥掩码为 ****<最后4位>；空值返回 <not set>。"""
    if not key:
        return "<not set>"
    return "****" + key[-4:] if len(key) >= 4 else "****"

class CredentialPort(ABC):
    """凭据端口：get/set/clear/status（status 返回掩码形式）。"""
    @abstractmethod
    def get(self) -> str | None: ...
    @abstractmethod
    def set(self, key: str) -> None: ...
    @abstractmethod
    def clear(self) -> None: ...
    def status(self) -> str:
        return mask_key(self.get())

class EnvCredentialStore(CredentialPort):
    """基于环境变量的凭据存储（运行时注入，绝不烘焙进镜像/源码）。"""
    def get(self) -> str | None:
        return os.environ.get(ENV_VAR)
    def set(self, key: str) -> None:
        os.environ[ENV_VAR] = key
    def clear(self) -> None:
        os.environ.pop(ENV_VAR, None)

class KeyringCredentialStore(CredentialPort):
    """基于 keyring 后端的凭据存储（延后 import；本项目 is_deployed:false 未启用）。"""
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
        except self._kr.errors.PasswordDeleteError:
            pass  # entry already absent — idempotent clear