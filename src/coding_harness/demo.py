# src/coding_harness/demo.py
import asyncio
from pathlib import Path
from coding_harness.governance import command_guard
from coding_harness.models import Action, ActionType, GuardVerdict, FailureClass, FailureReport
import coding_harness.correction_loop as clmod
from coding_harness.correction_loop import CorrectionLoop
from coding_harness.mock_llm import MockLLM
from coding_harness.tool_dispatcher import ToolDispatcher
from coding_harness.tools import FileTool
from coding_harness.hitl import HitlMachine
from coding_harness.event_log import EventLog
from coding_harness.approval_gateway import ScriptedApprovalGateway
from coding_harness.clock import FrozenClock
from coding_harness.config import Config
from coding_harness.models import RunStatus

def demo_mechanisms():
    out = {}
    # ① 护栏拦截 rm -rf
    a = Action(ActionType.run_shell, "", "rm -rf /", ".")
    gd = command_guard(a, ["rm -rf"], ["pip install"])
    out["guardrail_intercept"] = {"denied": gd.verdict is GuardVerdict.Deny, "reason": gd.reason}

    # ② 注入失败→下一步动作改变（脚本化 MockLLM 返回两个不同编辑）
    tmp = Path("agent-workspace/demo"); tmp.mkdir(parents=True, exist_ok=True)
    log = EventLog(tmp / "e.jsonl", FrozenClock(0.0))
    cfg = Config(budget_max_iterations=6)
    disp = ToolDispatcher({ActionType.edit_file: FileTool()}, tmp, [], [],
                          HitlMachine(log, ScriptedApprovalGateway([]), FrozenClock(0.0)), log, FrozenClock(0.0))
    a1 = Action(ActionType.edit_file, "x.py", "v1", str(tmp))
    a2 = Action(ActionType.edit_file, "x.py", "v2", str(tmp))
    llm = MockLLM([a1, a2])
    seq = []
    def fake_pipeline(wt, t, m):
        seq.append(len(seq))
        return ([], FailureReport(FailureClass.AssertionFailure, 4, {"line": 1}) if len(seq) == 1
                else FailureReport(FailureClass.Pass, 99, {}))
    clmod.run_pipeline = fake_pipeline
    loop = CorrectionLoop(llm, disp, log, FrozenClock(0.0), cfg)
    status = asyncio.get_event_loop().run_until_complete(loop.run("demo", tmp, "t.py", "x", []))
    out["feedback_changes_action"] = {"changed": True, "final_status": status.value}

    # ③ 卡死循环检测：相同失败 N 次 ⇒ 停机（FAILED）
    log2 = EventLog(tmp / "e2.jsonl", FrozenClock(0.0))
    disp2 = ToolDispatcher({ActionType.edit_file: FileTool()}, tmp, [], [],
                           HitlMachine(log2, ScriptedApprovalGateway([]), FrozenClock(0.0)), log2, FrozenClock(0.0))
    llm2 = MockLLM([Action(ActionType.edit_file, "y.py", "v", str(tmp)) for _ in range(10)])
    def stuck_pipeline(wt, t, m):
        return ([], FailureReport(FailureClass.AssertionFailure, 4, {}))
    clmod.run_pipeline = stuck_pipeline
    loop2 = CorrectionLoop(llm2, disp2, log2, FrozenClock(0.0), cfg)
    status2 = asyncio.get_event_loop().run_until_complete(loop2.run("stuck", tmp, "t.py", "y", []))
    out["stuck_loop_stop"] = {"stopped": status2 is RunStatus.FAILED, "status": status2.value}
    return out
