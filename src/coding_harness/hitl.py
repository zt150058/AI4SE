"""人在回路（HITL）：风险操作暂停-恢复状态机 + 审批检查点。

request() 把状态置 PAUSED、写 ApprovalRequested 事件并打检查点（恢复锚），
等网关返回后写 ApprovalReceived 并恢复 RUNNING。
"""
import asyncio
from enum import Enum
from coding_harness.models import Action, Approval, ApprovalStatus, EventType
from coding_harness.event_log import EventLog
from coding_harness.approval_gateway import ApprovalGateway
from coding_harness.clock import ClockPort

class HitlState(str, Enum):
    """HITL 状态：运行中 / 暂停等待审批。"""
    RUNNING = "RUN_RUNNING"
    PAUSED = "RUN_PAUSED"

class HitlMachine:
    """HITL 状态机：协调事件日志、审批网关与时钟。"""
    def __init__(self, event_log: EventLog, gateway: ApprovalGateway, clock: ClockPort) -> None:
        self._log = event_log
        self._gw = gateway
        self._clock = clock
        self.state = HitlState.RUNNING

    async def request(self, action: Action, run_id: str, reason: str, preview: str) -> ApprovalStatus:
        """暂停并请求审批；先打检查点（便于恢复），再等待网关返回。"""
        self.state = HitlState.PAUSED
        ap = Approval(id=f"ap-{self._clock.now()}", run_id=run_id, action=action,
                      reason=reason, preview=preview, status=ApprovalStatus.pending)
        self._log.append(run_id, EventType.ApprovalRequested,
                         {"reason": reason, "preview": preview})
        # 检查点须在等待审批之前标记，作为恢复锚点
        self._log.mark_checkpoint(run_id, self._log.events_for(run_id)[-1].seq)
        status = await self._gw.request(ap)
        self._log.append(run_id, EventType.ApprovalReceived, {"status": status.value})
        self.state = HitlState.RUNNING
        return status
