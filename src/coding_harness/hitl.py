# src/coding_harness/hitl.py
import asyncio
from enum import Enum
from coding_harness.models import Action, Approval, ApprovalStatus, EventType
from coding_harness.event_log import EventLog
from coding_harness.approval_gateway import ApprovalGateway
from coding_harness.clock import ClockPort

class HitlState(str, Enum):
    RUNNING = "RUN_RUNNING"
    PAUSED = "RUN_PAUSED"

class HitlMachine:
    def __init__(self, event_log: EventLog, gateway: ApprovalGateway, clock: ClockPort) -> None:
        self._log = event_log
        self._gw = gateway
        self._clock = clock
        self.state = HitlState.RUNNING

    async def request(self, action: Action, run_id: str, reason: str, preview: str) -> ApprovalStatus:
        self.state = HitlState.PAUSED
        ap = Approval(id=f"ap-{self._clock.now()}", run_id=run_id, action=action,
                      reason=reason, preview=preview, status=ApprovalStatus.pending)
        self._log.append(run_id, EventType.ApprovalRequested,
                         {"reason": reason, "preview": preview})
        self._log.mark_checkpoint(run_id, self._log.events_for(run_id)[-1].seq)
        status = await self._gw.request(ap)
        self._log.append(run_id, EventType.ApprovalReceived, {"status": status.value})
        self.state = HitlState.RUNNING
        return status
