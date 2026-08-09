# tests/test_agent_loop.py
import asyncio
from pathlib import Path
from coding_harness.agent_loop import AgentLoop, RunRequest
from coding_harness.correction_loop import CorrectionLoop
from coding_harness.mock_llm import MockLLM
from coding_harness.tool_dispatcher import ToolDispatcher
from coding_harness.tools import FileTool
from coding_harness.hitl import HitlMachine
from coding_harness.event_log import EventLog
from coding_harness.approval_gateway import ScriptedApprovalGateway
from coding_harness.clock import FrozenClock
from coding_harness.config import Config
from coding_harness.memory_store import SQLiteMemoryStore
from coding_harness.models import ActionType, RunStatus, EventType

FIX = Path(__file__).parent.parent / "fixtures" / "cart_repo"

def test_agent_loop_succeeds_when_correction_passes(tmp_path):
    log = EventLog(tmp_path/"e.jsonl", FrozenClock(0.0))
    cfg = Config()
    disp = ToolDispatcher({ActionType.edit_file: FileTool(), ActionType.read_file: FileTool()},
                          FIX, [], [], HitlMachine(log, ScriptedApprovalGateway([]), FrozenClock(0.0)),
                          log, FrozenClock(0.0))
    cl = CorrectionLoop(MockLLM([None]), disp, log, FrozenClock(0.0), cfg)
    import coding_harness.correction_loop as clmod
    from coding_harness.models import FailureClass, FailureReport
    clmod.run_pipeline = lambda wt, t, m: ([], FailureReport(FailureClass.Pass, 99, {}))
    mem = SQLiteMemoryStore(tmp_path/"m.db")
    agent = AgentLoop(cl, mem, log, FrozenClock(0.0), cfg)
    run = asyncio.get_event_loop().run_until_complete(
        agent.run(RunRequest(repo=str(FIX), target_test="test_cart.py", config=cfg)))
    assert run.status is RunStatus.SUCCEEDED
    assert any(e.type == EventType.RunFinished for e in log.events_for(run.id))
