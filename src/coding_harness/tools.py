"""工具实现：FileTool（读/写文件）+ ShellTool（执行命令，输出经密钥擦除）。

所有工具返回 ToolResult；ShellTool 在返回前对 stdout/stderr 调 redact，
并标记 redacted=True 以便上层可知发生过擦除。
"""
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from coding_harness.models import Action, ActionType, ToolResult
from coding_harness.redactor import redact

class ToolPort(ABC):
    """工具端口：execute(action) → ToolResult。"""
    @abstractmethod
    def execute(self, action: Action) -> ToolResult: ...

class FileTool(ToolPort):
    """文件工具：read_file 读 UTF-8 文本，edit_file 覆写目标文件。"""
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
    """shell 工具：执行命令，60s 超时，输出在返回前擦除密钥。"""
    def execute(self, action: Action) -> ToolResult:
        if action.type != ActionType.run_shell:
            return ToolResult(False, "", "not a shell action", 1)
        proc = subprocess.run(action.payload, shell=True, cwd=action.cwd or None,
                              capture_output=True, text=True, timeout=60)
        out = redact(proc.stdout)  # 防止 sk-ant- 密钥进入工具输出
        err = redact(proc.stderr)
        redacted = out != proc.stdout or err != proc.stderr  # 是否实际发生过擦除
        return ToolResult(proc.returncode == 0, out, err, proc.returncode, redacted=redacted)
