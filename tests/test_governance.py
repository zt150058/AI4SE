# tests/test_governance.py
from pathlib import Path
from coding_harness.governance import path_guard, command_guard
from coding_harness.models import Action, ActionType, GuardVerdict

def test_path_guard_allows_in_worktree(tmp_path):
    a = Action(ActionType.edit_file, str(tmp_path / "cart.py"), "x", str(tmp_path))
    assert path_guard(a, tmp_path).verdict is GuardVerdict.Allow

def test_path_guard_denies_escape(tmp_path):
    a = Action(ActionType.edit_file, str(tmp_path.parent / "outside.py"), "x", str(tmp_path))
    assert path_guard(a, tmp_path).verdict is GuardVerdict.Deny

def test_command_guard_denies_rm_rf():
    a = Action(ActionType.run_shell, "", "rm -rf /", ".")
    gd = command_guard(a, deny_patterns=["rm -rf"], approval_patterns=["pip install"])
    assert gd.verdict is GuardVerdict.Deny

def test_command_guard_requires_approval_for_pip():
    a = Action(ActionType.run_shell, "", "pip install requests", ".")
    gd = command_guard(a, deny_patterns=["rm -rf"], approval_patterns=["pip install"])
    assert gd.verdict is GuardVerdict.RequireApproval

def test_command_guard_allows_pytest():
    a = Action(ActionType.run_shell, "", "pytest -q", ".")
    gd = command_guard(a, deny_patterns=["rm -rf"], approval_patterns=["pip install"])
    assert gd.verdict is GuardVerdict.Allow
