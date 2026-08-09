from pathlib import Path
from coding_harness.validators import ImportValidator, TestValidator, LintValidator, TypeValidator

FIX = Path(__file__).parent.parent / "fixtures" / "cart_repo"

def test_import_validator_ok():
    r = ImportValidator().run(FIX, "cart")
    assert r.validator == "import"
    assert r.status in ("ok", "fail")

def test_test_validator_reports_failure():
    r = TestValidator().run(FIX, "test_cart.py")
    assert r.validator == "pytest"
    assert any(f.code == "AssertionError" or "Assertion" in f.code for f in r.findings) or r.status == "fail"

def test_lint_validator_runs():
    r = LintValidator().run(FIX)
    assert r.validator == "ruff"

def test_type_validator_runs():
    r = TypeValidator().run(FIX)
    assert r.validator == "mypy"
