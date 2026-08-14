"""记忆存储：SQLite 持久化跨运行的经验，供后续相关检索复用。

relevant() 按 repo + (convention 或命中失败类别) 检索记忆，用于在 AgentLoop
组装系统提示时注入历史经验。SQL 全参数化，无注入风险。
"""
import sqlite3
from abc import ABC, abstractmethod
from coding_harness.models import MemoryRecord

class MemoryStore(ABC):
    """记忆端口：put 写入、relevant 按 repo+失败类别检索。"""
    @abstractmethod
    def put(self, record) -> None: ...
    @abstractmethod
    def relevant(self, repo: str, failure_class) -> list: ...

class SQLiteMemoryStore(MemoryStore):
    """基于 SQLite 的记忆存储；表 memory(repo, kind, key, value, last_used)。"""
    def __init__(self, path) -> None:
        self._con = sqlite3.connect(str(path))
        self._con.execute("CREATE TABLE IF NOT EXISTS memory (repo TEXT, kind TEXT, key TEXT, value TEXT, last_used REAL)")
        self._con.commit()
    def put(self, record) -> None:
        self._con.execute("INSERT INTO memory VALUES (?,?,?,?,?)",
                          (record.repo, record.kind, str(record.key), record.value, record.last_used))
        self._con.commit()
    def relevant(self, repo: str, failure_class) -> list:
        """检索：该 repo 下，kind=convention（通用约定）或 key 命中失败类别者。"""
        key = getattr(failure_class, "value", str(failure_class))
        rows = self._con.execute(
            "SELECT * FROM memory WHERE repo=? AND (kind='convention' OR key=?)", (repo, key)).fetchall()
        from coding_harness.models import MemoryRecord
        return [MemoryRecord(r[0], r[1], r[2], r[3], r[4]) for r in rows]
