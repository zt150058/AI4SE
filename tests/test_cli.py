# tests/test_cli.py
from typer.testing import CliRunner
from coding_harness.cli import app

runner = CliRunner()

def test_credential_show_masks(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-abcdef123456")
    result = runner.invoke(app, ["credential", "show"])
    assert result.exit_code == 0
    assert "3456" in result.stdout
    assert "abcdef" not in result.stdout

def test_test_subcommand_dispatches_pytest(monkeypatch):
    # The `test` subcommand's job is to dispatch `pytest -q` and propagate its
    # exit code — NOT to run the suite here. Spawning a real pytest would
    # recursively run the whole project suite (incl. test_docker's multi-minute
    # docker build) and, on hosts where bare `pytest` resolves (Linux CI),
    # hang/fork-bomb the run. Real tool execution is exercised by test_docker
    # in CI; this is a unit test of the dispatch seam.
    seen = []
    def fake_call(cmd, **kwargs):
        seen.append(cmd)
        return 0
    monkeypatch.setattr("subprocess.call", fake_call)
    result = runner.invoke(app, ["test"])
    assert seen == [["pytest", "-q"]]
    assert result.exit_code == 0

def test_test_subcommand_propagates_nonzero_rc(monkeypatch):
    monkeypatch.setattr("subprocess.call", lambda cmd, **k: 1)
    result = runner.invoke(app, ["test"])
    assert result.exit_code == 1

def test_help_lists_subcommands():
    result = runner.invoke(app, ["--help"])
    assert "run" in result.stdout and "credential" in result.stdout
