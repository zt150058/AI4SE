import json
from dataclasses import asdict
from pathlib import Path
from coding_harness.clock import ClockPort
from coding_harness.models import Event, EventType


class EventLog:
    def __init__(self, path, clock: ClockPort) -> None:
        self._path = Path(path)
        self._clock = clock
        self._seq = 0
        self._checkpoints: dict[str, int] = {}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def append(self, run_id: str, event_type: EventType, payload: dict) -> Event:
        self._seq += 1
        ev = Event(seq=self._seq, run_id=run_id, type=event_type,
                   ts=self._clock.now(), payload=payload)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(ev), ensure_ascii=False) + "\n")
        return ev

    def events_for(self, run_id: str) -> list[Event]:
        out: list[Event] = []
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                if d["run_id"] == run_id:
                    out.append(Event(seq=d["seq"], run_id=d["run_id"],
                        type=EventType(d["type"]), ts=d["ts"], payload=d["payload"]))
        return out

    def mark_checkpoint(self, run_id: str, seq: int) -> None:
        self._checkpoints[run_id] = seq

    def latest_checkpoint(self, run_id: str) -> int | None:
        return self._checkpoints.get(run_id)