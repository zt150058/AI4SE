"""外层状态机 AgentLoop：组装上下文 → 驱动 CorrectionLoop → 落 Run/RunFinished。

把记忆事实注入系统提示，把请求转交 CorrectionLoop，并在事件日志中记录
StepStarted（repo 经 redact）与 RunFinished。Run 的 iters_used/tokens_used
当前固定 0（实际用量由 CorrectionLoop 内部计数，跨模块透传待后续）。
"""
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
    """一次运行请求：仓库、目标测试、配置（module 可选）。"""
    repo: str
    target_test: str
    config: Config
    module: str | None = None

class AgentLoop:
    """外层编排器：组合记忆 + CorrectionLoop + 事件日志。"""
    def __init__(self, correction: CorrectionLoop, memory: MemoryStore,
                 event_log: EventLog, clock: ClockPort, config: Config) -> None:
        self._corr = correction; self._mem = memory; self._log = event_log
        self._clock = clock; self._cfg = config

    async def run(self, request: RunRequest) -> Run:
        """执行一次运行：起 run_id → 注入记忆 → 驱动修正回路 → 收尾。"""
        run_id = f"run-{self._clock.now()}"
        # repo 在进入事件日志前脱敏（本地路径，非密钥，但保持一致处理）
        self._log.append(run_id, EventType.StepStarted, {"repo": redact(request.repo), "test": request.target_test})
        context = [{"role": "system", "content": f"Fix failing test {request.target_test} in {request.repo}."}]
        # 注入相关记忆事实（约定/历史经验）到系统提示
        facts = self._mem.relevant(request.repo, "convention")
        context.append({"role": "system", "content": "conventions: " + ", ".join(r.value for r in facts)})
        module = request.module or _infer_module(request.repo, request.target_test)
        status = await self._corr.run(run_id, request.repo, request.target_test, module, context)
        run = Run(id=run_id, status=status, repo=request.repo, target_test=request.target_test,
                  started_at=self._clock.now(), iters_used=0, tokens_used=0)
        self._log.append(run_id, EventType.RunFinished, {"status": status.value})
        return run

def _infer_module(repo, target_test):
    """从测试文件名推断被测模块名（去 test_ 前缀与扩展名）。"""
    name = target_test.split("/")[-1].replace("test_", "").replace(".py", "")
    return name
