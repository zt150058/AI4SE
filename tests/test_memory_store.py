# tests/test_memory_store.py
from coding_harness.memory_store import SQLiteMemoryStore, MemoryRecord
from coding_harness.models import FailureClass

def test_put_and_relevant(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "m.db")
    store.put(MemoryRecord("repo", "convention", "test_cmd", "pytest -q", 0.0))
    rec = MemoryRecord("repo", "fix_pattern", FailureClass.AssertionFailure.value, "off-by-one in sum", 0.0)
    store.put(rec)
    hits = store.relevant("repo", FailureClass.AssertionFailure)
    assert any("off-by-one" in r.value for r in hits)
    assert all(r.repo == "repo" for r in hits)
