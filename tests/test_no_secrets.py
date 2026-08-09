import re
from pathlib import Path

def test_no_real_key_shape_in_tracked_files():
    pat = re.compile(r"sk-ant-[A-Za-z0-9]{6,}")
    bad = []
    for p in Path(".").rglob("*"):
        if ".git" in p.parts: continue
        try: t = p.read_text(encoding="utf-8")
        except Exception: continue
        if pat.search(t): bad.append(str(p))
    assert not bad, f"found real-shape keys in: {bad}"