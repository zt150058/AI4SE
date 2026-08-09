from abc import ABC, abstractmethod
from dataclasses import dataclass
from coding_harness.models import Action

@dataclass
class LLMResponse:
    text: str
    tool_call: Action | None
    tokens_used: int

class LLMPort(ABC):
    @abstractmethod
    def complete(self, messages: list[dict], tools: list[dict]) -> LLMResponse: ...
