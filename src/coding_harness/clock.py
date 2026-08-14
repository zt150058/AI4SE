"""时钟抽象（注入式时间，便于在事件日志中打时间戳并支持测试冻结）。"""
import time
from abc import ABC, abstractmethod


class ClockPort(ABC):
    """时钟端口：生产用 SystemClock，测试用 FrozenClock 注入确定性时间。"""
    @abstractmethod
    def now(self) -> float: ...


class SystemClock(ClockPort):
    """基于系统墙钟的真实时钟。"""
    def now(self) -> float:
        return time.time()


class FrozenClock(ClockPort):
    """测试用冻结时钟：返回固定时间，advance 可手动推进。"""
    def __init__(self, t: float = 0.0) -> None:
        self._t = t

    def now(self) -> float:
        return self._t

    def advance(self, dt: float) -> None:
        self._t += dt
