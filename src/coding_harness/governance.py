# src/coding_harness/governance.py
from pathlib import Path
from coding_harness.models import Action, ActionType, GuardVerdict, GuardDecision

def _resolve(action: Action, worktree_root: Path) -> Path:
    base = (worktree_root / action.cwd).resolve() if action.cwd else worktree_root.resolve()
    target = (base / action.target).resolve() if action.target else base
    return target

def path_guard(action: Action, worktree_root: Path) -> GuardDecision:
    if action.type in (ActionType.edit_file, ActionType.read_file):
        root = worktree_root.resolve()
        tgt = _resolve(action, worktree_root)
        try:
            tgt.relative_to(root)
        except ValueError:
            return GuardDecision(GuardVerdict.Deny, f"path escapes worktree: {tgt}")
    return GuardDecision(GuardVerdict.Allow, "within worktree")

def command_guard(action: Action, deny_patterns: list[str], approval_patterns: list[str]) -> GuardDecision:
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
