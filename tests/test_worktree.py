# tests/test_worktree.py
from pathlib import Path
from coding_harness.worktree import create_worktree

def test_create_worktree(tmp_path):
    src = tmp_path / "repo"; src.mkdir()
    import subprocess
    subprocess.run(["git","init","-q"], cwd=src, check=True)
    (src/"a.txt").write_text("x")
    subprocess.run(["git","add","."], cwd=src, check=True)
    subprocess.run(["git","-c","user.email=t@t","-c","user.name=t","commit","-qm","init"], cwd=src, check=True)
    wt = create_worktree(tmp_path / "ws", "run1", src)
    assert (wt / "a.txt").exists()
    assert wt != src
