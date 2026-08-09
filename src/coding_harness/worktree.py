# src/coding_harness/worktree.py
import subprocess
from pathlib import Path

def create_worktree(root: Path, run_id: str, source_repo: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    target = root / run_id
    subprocess.run(["git", "worktree", "add", "--detach", str(target)],
                   cwd=source_repo, check=True, capture_output=True)
    return target
