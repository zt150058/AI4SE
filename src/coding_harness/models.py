"""数据模型与枚举层（贯穿全 harness 的共享类型定义）。

本模块集中定义所有 dataclass 与 Enum，其余模块通过组合这些类型协作，
避免跨模块循环依赖。Action 描述 LLM 提议的工具调用；Finding/ValidatorResult/
FailureReport 描述校验结果与失败分类；Event/Run 描述运行轨迹与状态。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionType(str, Enum):
    """LLM 可提议的工具动作类型。"""
    edit_file = "edit_file"
    run_shell = "run_shell"
    run_tests = "run_tests"
    read_file = "read_file"


@dataclass
class Action:
    """LLM 提议的一次工具调用（目标 + 载荷 + 工作目录）。"""
    type: ActionType
    target: str
    payload: str
    cwd: str


@dataclass
class ToolResult:
    """工具执行结果；redacted 标记 stdout/stderr 是否被密钥擦除。"""
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
    """失败分类（classifier 据此决定反馈注入与停机判定）。"""
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
    """事件日志类型（EventLog 顺序记录运行轨迹，供可观测/回放）。"""
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
    """运行终态（CorrectionLoop/AgentLoop 的停机结果）。"""
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
    """工具围栏判定：放行 / 拒绝 / 需人工审批。"""
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