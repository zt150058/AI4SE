# src/coding_harness/tools.py
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from coding_harness.models import Action, ActionType, ToolResult
from coding_harness.redactor import redact

class ToolPort(ABC):
    @abstractmethod
    def execute(self, action: Action) -> ToolResult: ...

class FileTool(ToolPort):
    def execute(self, action: Action) -> ToolResult:
        base = Path(action.cwd)
        path = base / action.target
        if action.type == ActionType.read_file:
            try:
                return ToolResult(True, path.read_text(encoding="utf-8"), "", 0)
            except FileNotFoundError as e:
                return ToolResult(False, "", str(e), 1)
        if action.type == ActionType.edit_file:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(action.payload, encoding="utf-8")
            return ToolResult(True, "", "", 0)
        return ToolResult(False, "", f"unsupported {action.type}", 1)

class ShellTool(ToolPort):
    def execute(self, action: Action) -> ToolResult:
        if action.type != ActionType.run_shell:
            return ToolResult(False, "", "not a shell action", 1)
        proc = subprocess.run(action.payload, shell=True, cwd=action.cwd or None,
                              capture_output=True, text=True, timeout=60)
        out = redact(proc.stdout)
        err = redact(proc.stderr)
        redacted = out != proc.stdout or err != proc.stderr
        return ToolResult(proc.returncode == 0, out, err, proc.returncode, redacted=redacted)
