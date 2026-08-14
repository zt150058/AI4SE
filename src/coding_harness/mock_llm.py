"""确定性 MockLLM：按预置脚本顺序返回动作，用于测试与机制演示。

脚本耗尽会抛 IndexError（CorrectionLoop 据此停机）；脚本项为 None 表示
LLM 不提议动作，对应 SUCCEEDED 停机分支。tokens_used 固定 10（仅作计数占位）。
"""
from coding_harness.llm_port import LLMPort, LLMResponse
from coding_harness.models import Action

class MockLLM(LLMPort):
    """脚本化 LLM：每次 complete 吐出脚本下一项，确定性可断言。"""
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
