# tests/test_approval_gateway.py
import asyncio
from coding_harness.approval_gateway import ScriptedApprovalGateway, ConsoleApprovalGateway
from coding_harness.models import Approval, ApprovalStatus

def _ap():
    return Approval(id="a1", run_id="r1", action=None, reason="pip install", preview="x", status=ApprovalStatus.pending)

def test_scripted_returns_in_order():
    gw = ScriptedApprovalGateway([ApprovalStatus.approved, ApprovalStatus.denied])
    assert asyncio.get_event_loop().run_until_complete(gw.request(_ap())) == ApprovalStatus.approved
    assert asyncio.get_event_loop().run_until_complete(gw.request(_ap())) == ApprovalStatus.denied

def test_console_noninteractive_denies(monkeypatch):
    gw = ConsoleApprovalGateway(timeout_minutes=1, interactive=False)
    assert asyncio.get_event_loop().run_until_complete(gw.request(_ap())) == ApprovalStatus.denied
