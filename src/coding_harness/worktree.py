"""工作树隔离：为一次运行创建 detached git worktree，避免污染源仓库。

create_worktree 在 source_repo 中执行 `git worktree add --detach`，
产出独立目录供本次运行编辑，互不干扰。
"""
import subprocess
from pathlib import Path

def create_worktree(root: Path, run_id: str, source_repo: Path) -> Path:
    """在 root/<run_id> 创建 detached worktree，返回其路径。"""
    root.mkdir(parents=True, exist_ok=True)
    target = root / run_id
    subprocess.run(["git", "worktree", "add", "--detach", str(target)],
                   cwd=source_repo, check=True, capture_output=True)
    return target
