# src/coding_harness/approval_gateway.py
import asyncio
import sys
from abc import ABC, abstractmethod
from coding_harness.models import Approval, ApprovalStatus

class ApprovalGateway(ABC):
    @abstractmethod
    async def request(self, approval: Approval) -> ApprovalStatus: ...

class ScriptedApprovalGateway(ApprovalGateway):
    def __init__(self, responses: list[ApprovalStatus]) -> None:
        self._r = list(responses); self._i = 0
    async def request(self, approval: Approval) -> ApprovalStatus:
        if self._i >= len(self._r):
            raise IndexError("scripted approvals exhausted")
        v = self._r[self._i]; self._i += 1; return v

class ConsoleApprovalGateway(ApprovalGateway):
    def __init__(self, timeout_minutes: int, interactive: bool | None = None) -> None:
        self._timeout = timeout_minutes
        self._interactive = sys.stdin.isatty() if interactive is None else interactive
    async def request(self, approval: Approval) -> ApprovalStatus:
        if not self._interactive:
            return ApprovalStatus.denied
        print(f"\n[APPROVAL REQUIRED] {approval.reason}\npreview: {approval.preview}")
        try:
            ans = await asyncio.wait_for(asyncio.to_thread(input, "approve? [y/N]: "), timeout=self._timeout*60)
        except (asyncio.TimeoutError, EOFError):
            return ApprovalStatus.timeout
        return ApprovalStatus.approved if ans.strip().lower() == "y" else ApprovalStatus.denied
