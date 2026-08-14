"""CLI 渲染器：把事件日志中的 Event 渲染为单行可读输出。"""
from coding_harness.models import Event

class CliRenderer:
    """事件→单行字符串渲染（[seq] TYPE payload）。"""
    @staticmethod
    def render(event: Event) -> str:
        return f"[{event.seq}] {event.type.value} {event.payload}"
