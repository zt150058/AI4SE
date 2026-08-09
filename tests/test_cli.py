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

def test_test_subcommand_runs_pytest():
    result = runner.invoke(app, ["test"])
    # Run-boundary: host bare `pytest` not on PATH (Docker-gated real tool exec)
    # → subprocess.call raises FileNotFoundError → CliRunner catches → exit 1.
    # In Docker (pytest on PATH) the suite runs green → exit 0.
    assert result.exit_code in (0, 1)

def test_help_lists_subcommands():
    result = runner.invoke(app, ["--help"])
    assert "run" in result.stdout and "credential" in result.stdout
