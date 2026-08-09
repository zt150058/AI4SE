# tests/test_tool_dispatcher.py
import asyncio
from pathlib import Path
from coding_harness.tool_dispatcher import ToolDispatcher
from coding_harness.tools import FileTool, ShellTool
from coding_harness.hitl import HitlMachine
from coding_harness.event_log import EventLog
from coding_harness.approval_gateway import ScriptedApprovalGateway
from coding_harness.clock import FrozenClock
from coding_harness.models import Action, ActionType, ApprovalStatus, EventType

def _make(tmp_path, approvals):
    log = EventLog(tmp_path/"e.jsonl", FrozenClock(0.0))
    hitl = HitlMachine(log, ScriptedApprovalGateway(approvals), FrozenClock(0.0))
    d = ToolDispatcher({ActionType.edit_file: FileTool(), ActionType.read_file: FileTool(),
                        ActionType.run_shell: ShellTool()}, tmp_path,
                       ["rm -rf"], ["pip install"], hitl, log, FrozenClock(0.0))
    return d, log

def test_dispatch_edit_allowed(tmp_path):
    d, log = _make(tmp_path, [])
    a = Action(ActionType.edit_file, "f.txt", "hi", str(tmp_path))
    r = asyncio.get_event_loop().run_until_complete(d.dispatch(a, "r1"))
    assert r.ok
    assert any(e.type == EventType.EditApplied for e in log.events_for("r1"))

def test_dispatch_deny_rm_rf(tmp_path):
    d, _ = _make(tmp_path, [])
    a = Action(ActionType.run_shell, "", "rm -rf /", ".")
    r = asyncio.get_event_loop().run_until_complete(d.dispatch(a, "r1"))
    assert not r.ok and "deny" in r.stderr.lower()

def test_dispatch_approval_denied_returns_synthetic(tmp_path):
    d, _ = _make(tmp_path, [ApprovalStatus.denied])
    a = Action(ActionType.run_shell, "", "pip install x", ".")
    r = asyncio.get_event_loop().run_until_complete(d.dispatch(a, "r1"))
    assert not r.ok and "denied" in r.stderr.lower()

def test_dispatch_approval_approved_runs(tmp_path):
    d, _ = _make(tmp_path, [ApprovalStatus.approved])
    a = Action(ActionType.run_shell, "", "echo ok", ".")
    r = asyncio.get_event_loop().run_until_complete(d.dispatch(a, "r1"))
    assert r.ok and "ok" in r.stdout
