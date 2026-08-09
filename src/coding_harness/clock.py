import time
from abc import ABC, abstractmethod


class ClockPort(ABC):
    @abstractmethod
    def now(self) -> float: ...


class SystemClock(ClockPort):
    def now(self) -> float:
        return time.time()


class FrozenClock(ClockPort):
    def __init__(self, t: float = 0.0) -> None:
        self._t = t

    def now(self) -> float:
        return self._t

    def advance(self, dt: float) -> None:
        self._t += dt
