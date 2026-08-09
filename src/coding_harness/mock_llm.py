from coding_harness.llm_port import LLMPort, LLMResponse
from coding_harness.models import Action

class MockLLM(LLMPort):
    def __init__(self, script: list) -> None:
        self._script = list(script)
        self._i = 0
    def complete(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        if self._i >= len(self._script):
            raise IndexError("MockLLM script exhausted")
        item = self._script[self._i]
        self._i += 1
        if item is None:
            return LLMResponse(text="(no action)", tool_call=None, tokens_used=10)
        return LLMResponse(text=f"apply {item.target}", tool_call=item, tokens_used=10)
