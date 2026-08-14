"""修正回路状态机（本项目主要贡献）。

CorrectionLoop 是确定性反馈回路的核心：反复「LLM 提出编辑 → 执行 →
运行校验器 → 分类失败 → 注入反馈 → 重试」，在四种停机条件下终止：
Pass（通过）、预算耗尽（BUDGET_HIT）、卡死循环（FAILED）、LLM 无动作（SUCCEEDED）。
"""
import asyncio
from enum import Enum
from coding_harness.models import RunStatus, EventType, FailureClass
from coding_harness.event_log import EventLog
from coding_harness.clock import ClockPort
from coding_harness.config import Config
from coding_harness.llm_port import LLMPort
from coding_harness.tool_dispatcher import ToolDispatcher

class CorrectionState(str, Enum):
    """修正回路的状态枚举（用于事件日志可观测与调试）。"""
    IDLE = "IDLE"; EDIT_APPLIED = "EDIT_APPLIED"; VALIDATING = "VALIDATING"
    DONE = "DONE"; BUDGET_HIT = "BUDGET_HIT"; FEEDBACK_PREPARED = "FEEDBACK_PREPARED"; RETRY = "RETRY"

STUCK_N = 3  # 连续相同失败次数 ⇒ 卡死

class CorrectionLoop:
    """确定性修正回路：驱动 编辑→校验→分类→反馈 的反馈循环。"""

    def __init__(self, llm: LLMPort, dispatcher: ToolDispatcher, event_log: EventLog,
                 clock: ClockPort, config: Config) -> None:
        self._llm = llm; self._disp = dispatcher; self._log = event_log
        self._clock = clock; self._cfg = config
        self.state = CorrectionState.IDLE

    async def run(self, run_id, worktree, target_test, module, context):
        """执行修正回路直至停机。

        停机条件（按检测顺序）：
        - LLM 无后续动作 ⇒ SUCCEEDED
        - 校验通过（FailureClass.Pass）⇒ SUCCEEDED
        - 迭代/Token 预算耗尽 ⇒ BUDGET_HIT
        - 同一类失败连续重复 STUCK_N 次 ⇒ FAILED（卡死循环）
        """
        tokens = 0; iters = 0; last_class = None; repeats = 0
        self.state = CorrectionState.IDLE
        while True:
            self._log.append(run_id, EventType.LoopIterated, {"iter": iters})
            self.state = CorrectionState.IDLE
            resp = self._llm.complete(messages=context, tools=[])
            tokens += resp.tokens_used
            self._log.append(run_id, EventType.TokenBudgetTick, {"tokens": tokens})
            if resp.tool_call is None:
                self.state = CorrectionState.DONE
                return RunStatus.SUCCEEDED  # 停机①：LLM 无后续动作
            await self._disp.dispatch(resp.tool_call, run_id)
            self.state = CorrectionState.EDIT_APPLIED
            self.state = CorrectionState.VALIDATING
            results, fr = run_pipeline(worktree, target_test, module)
            self._log.append(run_id, EventType.ValidatorResult,
                             {"results": [{"validator": r.validator, "status": r.status} for r in results]})
            self._log.append(run_id, EventType.FailureClassified, {"class": fr.klass.value, "priority": fr.priority})
            iters += 1
            if fr.klass is FailureClass.Pass:
                self.state = CorrectionState.DONE
                return RunStatus.SUCCEEDED  # 停机②：校验通过
            if iters >= self._cfg.budget_max_iterations or tokens >= self._cfg.budget_max_tokens:
                self.state = CorrectionState.BUDGET_HIT
                return RunStatus.BUDGET_HIT  # 停机③：预算耗尽
            if fr.klass == last_class:
                repeats += 1
                if repeats >= STUCK_N:
                    self.state = CorrectionState.BUDGET_HIT
                    return RunStatus.FAILED  # 停机④：卡死循环（同类失败连续重复）
            else:
                repeats = 0
            last_class = fr.klass
            self.state = CorrectionState.FEEDBACK_PREPARED
            context.append({"role": "system", "content": f"FAIL class={fr.klass.value} priority={fr.priority} {fr.payload}"})
            self.state = CorrectionState.RETRY

# 模块级导入，便于测试 monkeypatch coding_harness.correction_loop.run_pipeline
from coding_harness.validator_pipeline import run_pipeline  # noqa: E402
