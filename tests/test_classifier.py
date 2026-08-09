# tests/test_classifier.py
from coding_harness.classifier import classify
from coding_harness.models import ValidatorResult, Finding, FailureClass

def test_all_pass():
    rs = [ValidatorResult("import","ok",[]), ValidatorResult("pytest","ok",[])]
    assert classify(rs).klass is FailureClass.Pass

def test_import_failure_short_circuits():
    rs = [ValidatorResult("import","fail",[Finding("m",0,"ImportError","no module","")]),
          ValidatorResult("pytest","fail",[Finding("t",0,"AssertionError","x","")])]
    fr = classify(rs)
    assert fr.klass is FailureClass.ImportError

def test_assertion_when_imports_ok():
    rs = [ValidatorResult("import","ok",[]),
          ValidatorResult("pytest","fail",[Finding("t",42,"AssertionError","assert 9","")])]
    fr = classify(rs)
    assert fr.klass is FailureClass.AssertionFailure
    assert fr.payload["line"] == 42

def test_lint_blocker_when_tests_ok():
    rs = [ValidatorResult("import","ok",[]), ValidatorResult("pytest","ok",[]),
          ValidatorResult("ruff","fail",[Finding("a.py",3,"F401","unused","")])]
    assert classify(rs).klass is FailureClass.LintBlocker
