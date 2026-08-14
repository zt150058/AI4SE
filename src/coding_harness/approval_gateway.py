"""审批网关：风险操作暂停等待人工确认。Scripted（测试）+ Console（交互）。

非交互模式（无 tty）默认 denied——CI/容器等无人值守场景下，风险操作不会被自动放行。
"""
import asyncio
import sys
from abc import ABC, abstractmethod
from coding_harness.models import Approval, ApprovalStatus

class ApprovalGateway(ABC):
    """审批端口：request(approval) → ApprovalStatus。"""
    @abstractmethod
    async def request(self, approval: Approval) -> ApprovalStatus: ...

class ScriptedApprovalGateway(ApprovalGateway):
    """脚本化网关：按预置序列返回审批结果，确定性可断言。"""
    def __init__(self, responses: list[ApprovalStatus]) -> None:
        self._r = list(responses); self._i = 0
    async def request(self, approval: Approval) -> ApprovalStatus:
        if self._i >= len(self._r):
            raise IndexError("scripted approvals exhausted")
        v = self._r[self._i]; self._i += 1; return v

class ConsoleApprovalGateway(ApprovalGateway):
    """控制台网关：有 tty 时阻塞读取 y/N，超时记 timeout；无 tty 默认 denied。"""
    def __init__(self, timeout_minutes: int, interactive: bool | None = None) -> None:
        self._timeout = timeout_minutes
        self._interactive = sys.stdin.isatty() if interactive is None else interactive
    async def request(self, approval: Approval) -> ApprovalStatus:
        if not self._interactive:
            return ApprovalStatus.denied  # 非交互（无 tty）→ 默认拒绝，永不自动放行风险操作
        print(f"\n[APPROVAL REQUIRED] {approval.reason}\npreview: {approval.preview}")
        try:
            ans = await asyncio.wait_for(asyncio.to_thread(input, "approve? [y/N]: "), timeout=self._timeout*60)
        except (asyncio.TimeoutError, EOFError):
            return ApprovalStatus.timeout
        return ApprovalStatus.approved if ans.strip().lower() == "y" else ApprovalStatus.denied
