"""工具围栏：路径围栏 + 命令围栏，对工具作用域做 Allow/Deny/RequireApproval 判定。

path_guard 防止文件操作逃逸出 worktree（路径穿越）；command_guard 按
deny/approval 模式串匹配对 shell 命令分级（如 rm -rf 拒绝、pip install 需审批）。
"""
from pathlib import Path
from coding_harness.models import Action, ActionType, GuardVerdict, GuardDecision

def _resolve(action: Action, worktree_root: Path) -> Path:
    """将 action 的相对 cwd/target 解析为绝对路径（用于围栏校验）。"""
    base = (worktree_root / action.cwd).resolve() if action.cwd else worktree_root.resolve()
    target = (base / action.target).resolve() if action.target else base
    return target

def path_guard(action: Action, worktree_root: Path) -> GuardDecision:
    """文件类动作的路径围栏：目标若逃逸出 worktree 根则 Deny。"""
    if action.type in (ActionType.edit_file, ActionType.read_file):
        root = worktree_root.resolve()
        tgt = _resolve(action, worktree_root)
        try:
            tgt.relative_to(root)  # 不能逃逸到 worktree 之外
        except ValueError:
            return GuardDecision(GuardVerdict.Deny, f"path escapes worktree: {tgt}")
    return GuardDecision(GuardVerdict.Allow, "within worktree")

def command_guard(action: Action, deny_patterns: list[str], approval_patterns: list[str]) -> GuardDecision:
    """shell 命令围栏：命中 deny→拒绝，命中 approval→需审批，否则放行。"""
    if action.type != ActionType.run_shell:
        return GuardDecision(GuardVerdict.Allow, "non-shell action")
    cmd = action.payload
    for pat in deny_patterns:
        if pat in cmd:
            return GuardDecision(GuardVerdict.Deny, f"deny pattern matched: {pat}")
    for pat in approval_patterns:
        if pat in cmd:
            return GuardDecision(GuardVerdict.RequireApproval, f"approval pattern matched: {pat}")
    return GuardDecision(GuardVerdict.Allow, "command allowed")
