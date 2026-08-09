# src/coding_harness/classifier.py
from coding_harness.models import ValidatorResult, FailureClass, FailureReport

def classify(results: list[ValidatorResult]) -> FailureReport:
    res = {r.validator: r for r in results}
    imp = res.get("import")
    if imp and imp.status == "fail":
        f = imp.findings[0] if imp.findings else None
        return FailureReport(FailureClass.ImportError, 0, {"message": f.message if f else ""})
    tests = res.get("pytest")
    if tests and tests.status == "fail":
        f = (tests.findings[0] if tests.findings else None)
        code = f.code if f else ""
        if "Collection" in code:
            return FailureReport(FailureClass.CollectionError, 2, {})
        if "Name" in code:
            return FailureReport(FailureClass.NameError, 3, {"message": f.message if f else ""})
        if "Attribute" in code:
            return FailureReport(FailureClass.AttributeError, 4, {})
        if "Timeout" in code:
            return FailureReport(FailureClass.Timeout, 5, {})
        return FailureReport(FailureClass.AssertionFailure, 4,
                            {"line": f.line if f else 0, "snippet": f.snippet if f else ""})
    mypy = res.get("mypy")
    if mypy and mypy.status == "fail":
        f = mypy.findings[0] if mypy.findings else None
        return FailureReport(FailureClass.TypeError, 5, {"message": f.message if f else ""})
    ruff = res.get("ruff")
    if ruff and ruff.status == "fail":
        f = ruff.findings[0] if ruff.findings else None
        return FailureReport(FailureClass.LintBlocker, 6, {"code": f.code if f else ""})
    return FailureReport(FailureClass.Pass, 99, {})
