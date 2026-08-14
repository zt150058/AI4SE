"""工具分发器：围栏→审批→执行的总线，串起 governance + HITL + tools。

dispatch 顺序：path_guard 拒绝路径穿越 → command_guard 分级（Deny 直接拒、
RequireApproval 经 HITL 等审批）→ 查表执行工具 → 落 EditApplied 事件。
"""
import asyncio
from pathlib import Path
from coding_harness.governance import path_guard, command_guard
from coding_harness.hitl import HitlMachine
from coding_harness.event_log import EventLog
from coding_harness.clock import ClockPort
from coding_harness.models import Action, ActionType, ToolResult, GuardVerdict, EventType, ApprovalStatus

class ToolDispatcher:
    """工具分发总线：注入围栏模式、HITL、事件日志与时钟。"""
    def __init__(self, tools: dict, worktree_root: Path, deny_patterns: list[str],
                 approval_patterns: list[str], hitl: HitlMachine, event_log: EventLog,
                 clock: ClockPort) -> None:
        self._tools = tools; self._root = worktree_root
        self._deny = deny_patterns; self._appr = approval_patterns
        self._hitl = hitl; self._log = event_log; self._clock = clock

    async def dispatch(self, action: Action, run_id: str) -> ToolResult:
        """执行一次动作：先过路径/命令围栏，再按需审批，最后执行工具。"""
        # 路径围栏：拒绝逃逸出 worktree 的文件操作
        pg = path_guard(action, self._root)
        if pg.verdict is GuardVerdict.Deny:
            self._log.append(run_id, EventType.GuardDecision, {"verdict": "Deny", "reason": pg.reason})
            return ToolResult(False, "", f"denied: {pg.reason}", 1)
        # 命令围栏：分级 Deny / RequireApproval / Allow
        cg = command_guard(action, self._deny, self._appr)
        self._log.append(run_id, EventType.GuardDecision, {"verdict": cg.verdict.value, "reason": cg.reason})
        if cg.verdict is GuardVerdict.Deny:
            return ToolResult(False, "", f"denied: {cg.reason}", 1)
        if cg.verdict is GuardVerdict.RequireApproval:
            status = await self._hitl.request(action, run_id, cg.reason, action.payload)
            if status is not ApprovalStatus.approved:  # denied/timeout → 不执行
                return ToolResult(False, "", f"action denied: {cg.reason} ({status.value})", 1)
        tool = self._tools.get(action.type)
        if tool is None:
            return ToolResult(False, "", f"no tool for {action.type}", 1)
        result = tool.execute(action)
        if action.type == ActionType.edit_file:
            self._log.append(run_id, EventType.EditApplied, {"target": action.target})
        return result
