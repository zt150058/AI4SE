"""配置加载：从 YAML 读取运行配置，缺失键走 dataclass 默认值。"""
from dataclasses import dataclass, field
import yaml


@dataclass
class Config:
    """运行配置：预算、围栏模式、记忆存储路径、LLM 提供方等。"""
    worktree_root: str = "./agent-workspace"
    budget_max_iterations: int = 6
    budget_max_tokens: int = 50000
    deny_patterns: list[str] = field(default_factory=lambda: ["rm -rf", "git push --force"])
    approval_patterns: list[str] = field(default_factory=lambda: ["pip install", "git clone"])
    approval_timeout_minutes: int = 15
    lint_codes_blocking: list[str] = field(default_factory=lambda: ["E", "F"])
    memory_store_path: str = "./memory.db"
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-5"


DEFAULT_CONFIG = Config()


def load_config(path: str) -> Config:
    """从 YAML 文件加载配置；空文件返回全默认 Config。"""
    with open(path, "r", encoding="utf-8") as f:
        d = yaml.safe_load(f) or {}
    return Config(**d)
