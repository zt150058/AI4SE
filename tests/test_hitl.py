# tests/test_hitl.py
import asyncio
from coding_harness.hitl import HitlMachine, HitlState
from coding_harness.event_log import EventLog
from coding_harness.approval_gateway import ScriptedApprovalGateway
from coding_harness.clock import FrozenClock
from coding_harness.models import Action, ActionType, EventType, ApprovalStatus

def test_approve_flow_emits_events_and_resumes(tmp_path):
    log = EventLog(tmp_path / "e.jsonl", FrozenClock(0.0))
    gw = ScriptedApprovalGateway([ApprovalStatus.approved])
    m = HitlMachine(log, gw, FrozenClock(0.0))
    a = Action(ActionType.run_shell, "", "pip install x", ".")
    status = asyncio.get_event_loop().run_until_complete(
        m.request(a, run_id="r1", reason="pip install", preview="pip install x"))
    assert status == ApprovalStatus.approved
    assert m.state == HitlState.RUNNING
    types = [e.type for e in log.events_for("r1")]
    assert EventType.ApprovalRequested in types and EventType.ApprovalReceived in types

def test_timeout_marks_checkpoint(tmp_path):
    log = EventLog(tmp_path / "e.jsonl", FrozenClock(0.0))
    gw = ScriptedApprovalGateway([ApprovalStatus.timeout])
    m = HitlMachine(log, gw, FrozenClock(0.0))
    a = Action(ActionType.run_shell, "", "pip install x", ".")
    status = asyncio.get_event_loop().run_until_complete(
        m.request(a, run_id="r1", reason="pip", preview="x"))
    assert status == ApprovalStatus.timeout
    assert log.latest_checkpoint("r1") is not None
