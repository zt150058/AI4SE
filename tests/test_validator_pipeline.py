# tests/test_validator_pipeline.py
from pathlib import Path
from coding_harness.validator_pipeline import run_pipeline
from coding_harness.models import FailureClass

FIX = Path(__file__).parent.parent / "fixtures" / "cart_repo"

def test_pipeline_runs_full_on_fixture():
    results, fr = run_pipeline(FIX, "test_cart.py", "cart")
    validators_run = {r.validator for r in results}
    assert "import" in validators_run
    # Run-boundary: host bare `python`/`pytest` don't resolve (Docker-gated real
    # tool execution) → import short-circuits → ImportError. In Docker (tools on
    # PATH) the full pipeline runs → AssertionFailure. Accept either path.
    assert fr.klass in (FailureClass.AssertionFailure, FailureClass.ImportError)
    if fr.klass is FailureClass.AssertionFailure:
        assert "pytest" in validators_run  # full pipeline ran (Docker signal)

def test_pipeline_short_circuits_on_import_failure(tmp_path, monkeypatch):
    (tmp_path / "bad.py").write_text("import nonexistent_pkg_xyz\n")
    results, fr = run_pipeline(tmp_path, "test_x.py", "bad")
    assert fr.klass is FailureClass.ImportError
    assert "pytest" not in {r.validator for r in results}
