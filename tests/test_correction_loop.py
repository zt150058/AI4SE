# tests/test_correction_loop.py
import asyncio
from pathlib import Path
from coding_harness.correction_loop import CorrectionLoop, CorrectionState
from coding_harness.mock_llm import MockLLM
from coding_harness.tool_dispatcher import ToolDispatcher
from coding_harness.tools import FileTool
from coding_harness.hitl import HitlMachine
from coding_harness.event_log import EventLog
from coding_harness.approval_gateway import ScriptedApprovalGateway
from coding_harness.clock import FrozenClock
from coding_harness.config import Config
from coding_harness.models import Action, ActionType, RunStatus, EventType

FIX = Path(__file__).parent.parent / "fixtures" / "cart_repo"

def _loop(tmp_path, script, config=None):
    log = EventLog(tmp_path/"e.jsonl", FrozenClock(0.0))
    cfg = config or Config(budget_max_iterations=6, budget_max_tokens=100000)
    dispatcher = ToolDispatcher({ActionType.edit_file: FileTool(), ActionType.read_file: FileTool()},
                               FIX, [], [], HitlMachine(log, ScriptedApprovalGateway([]), FrozenClock(0.0)),
                               log, FrozenClock(0.0))
    return CorrectionLoop(MockLLM(script), dispatcher, log, FrozenClock(0.0), cfg), log

def test_pass_on_green_first_try(tmp_path):
    loop, log = _loop(tmp_path, [Action(ActionType.edit_file, "cart.py", "fix", str(FIX))])
    import coding_harness.correction_loop as cl
    cl.run_pipeline = lambda wt, t, m: ([], __import__("coding_harness.models", fromlist=["FailureReport"]).FailureReport(
        __import__("coding_harness.models", fromlist=["FailureClass"]).FailureClass.Pass, 99, {}))
    status = asyncio.get_event_loop().run_until_complete(loop.run("r1", FIX, "test_cart.py", "cart", []))
    assert status is RunStatus.SUCCEEDED
    types = [e.type for e in log.events_for("r1")]
    assert EventType.LoopIterated in types
