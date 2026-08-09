# src/coding_harness/cli_renderer.py
from coding_harness.models import Event

class CliRenderer:
    @staticmethod
    def render(event: Event) -> str:
        return f"[{event.seq}] {event.type.value} {event.payload}"
