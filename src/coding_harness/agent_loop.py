# src/coding_harness/agent_loop.py
from dataclasses import dataclass
from coding_harness.correction_loop import CorrectionLoop
from coding_harness.memory_store import MemoryStore
from coding_harness.event_log import EventLog
from coding_harness.clock import ClockPort
from coding_harness.config import Config
from coding_harness.models import Run, RunStatus, EventType
from coding_harness.redactor import redact

@dataclass
class RunRequest:
    repo: str
    target_test: str
    config: Config
    module: str | None = None

class AgentLoop:
    def __init__(self, correction: CorrectionLoop, memory: MemoryStore,
                 event_log: EventLog, clock: ClockPort, config: Config) -> None:
        self._corr = correction; self._mem = memory; self._log = event_log
        self._clock = clock; self._cfg = config

    async def run(self, request: RunRequest) -> Run:
        run_id = f"run-{self._clock.now()}"
        self._log.append(run_id, EventType.StepStarted, {"repo": redact(request.repo), "test": request.target_test})
        context = [{"role": "system", "content": f"Fix failing test {request.target_test} in {request.repo}."}]
        facts = self._mem.relevant(request.repo, "convention")
        context.append({"role": "system", "content": "conventions: " + ", ".join(r.value for r in facts)})
        module = request.module or _infer_module(request.repo, request.target_test)
        status = await self._corr.run(run_id, request.repo, request.target_test, module, context)
        run = Run(id=run_id, status=status, repo=request.repo, target_test=request.target_test,
                  started_at=self._clock.now(), iters_used=0, tokens_used=0)
        self._log.append(run_id, EventType.RunFinished, {"status": status.value})
        return run

def _infer_module(repo, target_test):
    name = target_test.split("/")[-1].replace("test_", "").replace(".py", "")
    return name
