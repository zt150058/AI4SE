# src/coding_harness/memory_store.py
import sqlite3
from abc import ABC, abstractmethod
from coding_harness.models import MemoryRecord

class MemoryStore(ABC):
    @abstractmethod
    def put(self, record) -> None: ...
    @abstractmethod
    def relevant(self, repo: str, failure_class) -> list: ...

class SQLiteMemoryStore(MemoryStore):
    def __init__(self, path) -> None:
        self._con = sqlite3.connect(str(path))
        self._con.execute("CREATE TABLE IF NOT EXISTS memory (repo TEXT, kind TEXT, key TEXT, value TEXT, last_used REAL)")
        self._con.commit()
    def put(self, record) -> None:
        self._con.execute("INSERT INTO memory VALUES (?,?,?,?,?)",
                          (record.repo, record.kind, str(record.key), record.value, record.last_used))
        self._con.commit()
    def relevant(self, repo: str, failure_class) -> list:
        key = getattr(failure_class, "value", str(failure_class))
        rows = self._con.execute(
            "SELECT * FROM memory WHERE repo=? AND (kind='convention' OR key=?)", (repo, key)).fetchall()
        from coding_harness.models import MemoryRecord
        return [MemoryRecord(r[0], r[1], r[2], r[3], r[4]) for r in rows]
