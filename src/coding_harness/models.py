from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionType(str, Enum):
    edit_file = "edit_file"
    run_shell = "run_shell"
    run_tests = "run_tests"
    read_file = "read_file"


@dataclass
class Action:
    type: ActionType
    target: str
    payload: str
    cwd: str


@dataclass
class ToolResult:
    ok: bool
    stdout: str
    stderr: str
    exit_code: int
    redacted: bool = False


@dataclass
class Finding:
    file: str
    line: int
    code: str
    message: str
    snippet: str


@dataclass
class ValidatorResult:
    validator: str
    status: str
    findings: list[Finding]


class FailureClass(str, Enum):
    ImportError = "ImportError"
    SyntaxError = "SyntaxError"
    NameError = "NameError"
    AttributeError = "AttributeError"
    AssertionFailure = "AssertionFailure"
    CollectionError = "CollectionError"
    Timeout = "Timeout"
    LintBlocker = "LintBlocker"
    TypeError = "TypeError"
    ParseError = "ParseError"
    Pass = "Pass"


@dataclass
class FailureReport:
    klass: FailureClass
    priority: int
    payload: dict


class EventType(str, Enum):
    StepStarted = "StepStarted"
    ActionProposed = "ActionProposed"
    GuardDecision = "GuardDecision"
    EditApplied = "EditApplied"
    ValidatorResult = "ValidatorResult"
    FailureClassified = "FailureClassified"
    ApprovalRequested = "ApprovalRequested"
    ApprovalReceived = "ApprovalReceived"
    LoopIterated = "LoopIterated"
    RunFinished = "RunFinished"
    TokenBudgetTick = "TokenBudgetTick"


@dataclass
class Event:
    seq: int
    run_id: str
    type: EventType
    ts: float
    payload: dict


class RunStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ERRORED = "ERRORED"
    BUDGET_HIT = "BUDGET_HIT"


@dataclass
class Run:
    id: str
    status: RunStatus
    repo: str
    target_test: str
    started_at: float
    iters_used: int
    tokens_used: int


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"
    timeout = "timeout"


@dataclass
class Approval:
    id: str
    run_id: str
    action: Action | None
    reason: str
    preview: str
    status: ApprovalStatus


class GuardVerdict(str, Enum):
    Allow = "Allow"
    Deny = "Deny"
    RequireApproval = "RequireApproval"


@dataclass
class GuardDecision:
    verdict: GuardVerdict
    reason: str


@dataclass
class MemoryRecord:
    repo: str
    kind: str
    key: str
    value: str
    last_used: float