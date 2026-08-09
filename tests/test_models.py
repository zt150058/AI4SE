# tests/test_models.py
from coding_harness.models import (
    Action, ActionType, ToolResult, Finding, ValidatorResult, FailureClass,
    FailureReport, EventType, Event, RunStatus, Run, ApprovalStatus, Approval,
    GuardVerdict, GuardDecision, MemoryRecord,
)


def test_action_and_result():
    a = Action(type=ActionType.edit_file, target="cart.py", payload="x", cwd=".")
    assert a.type == ActionType.edit_file
    r = ToolResult(ok=True, stdout="", stderr="", exit_code=0, redacted=False)
    assert r.ok is True


def test_failure_report_klass_field_named_klass():
    fr = FailureReport(klass=FailureClass.AssertionFailure, priority=4, payload={"line": 42})
    assert fr.klass is FailureClass.AssertionFailure
    assert fr.priority == 4


def test_event_types_complete():
    expected = {"StepStarted", "ActionProposed", "GuardDecision", "EditApplied",
                "ValidatorResult", "FailureClassified", "ApprovalRequested", "ApprovalReceived",
                "LoopIterated", "RunFinished", "TokenBudgetTick"}
    assert {e.value for e in EventType} == expected


def test_failure_class_enum_complete():
    names = {"ImportError", "SyntaxError", "NameError", "AttributeError",
             "AssertionFailure", "CollectionError", "Timeout", "LintBlocker",
             "TypeError", "ParseError", "Pass"}
    assert {c.value for c in FailureClass} == names


def test_guard_decision_and_approval():
    gd = GuardDecision(verdict=GuardVerdict.RequireApproval, reason="pip install")
    assert gd.verdict is GuardVerdict.RequireApproval
    ap = Approval(id="a1", run_id="r1", action=None, reason="x", preview="y", status=ApprovalStatus.pending)
    assert ap.status is ApprovalStatus.pending