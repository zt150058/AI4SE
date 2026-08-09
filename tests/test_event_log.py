from coding_harness.event_log import EventLog
from coding_harness.clock import FrozenClock
from coding_harness.models import EventType


def test_append_increments_seq_and_stamps_ts(tmp_path):
    log = EventLog(path=tmp_path / "e.jsonl", clock=FrozenClock(10.0))
    e1 = log.append("run1", EventType.StepStarted, {"i": 1})
    e2 = log.append("run1", EventType.RunFinished, {"ok": True})
    assert e1.seq == 1 and e2.seq == 2
    assert e1.ts == 10.0
    assert e1.run_id == "run1" and e1.type == EventType.StepStarted


def test_events_for_returns_in_order(tmp_path):
    log = EventLog(path=tmp_path / "e.jsonl", clock=FrozenClock(0.0))
    log.append("run1", EventType.StepStarted, {})
    log.append("run2", EventType.StepStarted, {})
    log.append("run1", EventType.RunFinished, {})
    evts = log.events_for("run1")
    assert [e.type for e in evts] == [EventType.StepStarted, EventType.RunFinished]


def test_checkpoint_roundtrip(tmp_path):
    log = EventLog(path=tmp_path / "e.jsonl", clock=FrozenClock(0.0))
    a = log.append("r", EventType.StepStarted, {})
    log.mark_checkpoint("r", a.seq)
    assert log.latest_checkpoint("r") == a.seq