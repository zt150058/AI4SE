# tests/test_tools.py
from coding_harness.tools import FileTool, ShellTool
from coding_harness.models import Action, ActionType

def test_file_tool_read(tmp_path):
    f = tmp_path / "a.txt"; f.write_text("hello")
    a = Action(ActionType.read_file, "a.txt", "", str(tmp_path))
    r = FileTool().execute(a)
    assert r.ok and r.stdout == "hello"

def test_file_tool_edit(tmp_path):
    a = Action(ActionType.edit_file, "b.txt", "new content", str(tmp_path))
    r = FileTool().execute(a)
    assert r.ok
    assert (tmp_path / "b.txt").read_text() == "new content"

def test_shell_tool_runs_echo():
    a = Action(ActionType.run_shell, "", "echo hi", ".")
    r = ShellTool().execute(a)
    assert r.ok and "hi" in r.stdout

def test_shell_tool_redacts_key(tmp_path):
    a = Action(ActionType.run_shell, "", "echo sk-ant-api03-secret1234", ".")
    r = ShellTool().execute(a)
    assert "secret1234" not in r.stdout
    assert r.redacted is True
