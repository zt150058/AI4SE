"""LLM 端口抽象：仅依赖 chat-completion + tool-call 原语，不寄生在代理框架上。

complete(messages, tools) 是整个 harness 与 LLM 交互的唯一接缝；
AnthropicLLM 真实适配器按计划延后（is_deployed:false），当前由 mock_llm 提供确定性实现。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from coding_harness.models import Action

@dataclass
class LLMResponse:
    """LLM 一次响应：文本、提议的工具调用（可能为 None）、Token 用量。"""
    text: str
    tool_call: Action | None
    tokens_used: int

class LLMPort(ABC):
    """LLM 端口：输入对话上下文+可用工具，输出一次响应。"""
    @abstractmethod
    def complete(self, messages: list[dict], tools: list[dict]) -> LLMResponse: ...
