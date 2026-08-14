"""失败分类器：把校验器结果归约为单一 FailureReport（类别 + 优先级）。

按优先级短路：导入失败 > 测试失败（细分为 Collection/Name/Attribute/Timeout/
Assertion）> 类型错误 > Lint 阻断 > Pass。CorrectionLoop 据类别决定反馈注入，
并据「同类失败是否连续重复」判断是否卡死。
"""
from coding_harness.models import ValidatorResult, FailureClass, FailureReport

def classify(results: list[ValidatorResult]) -> FailureReport:
    """将多个校验结果归约为一个 FailureReport（短路，按优先级取首个失败）。"""
    res = {r.validator: r for r in results}
    # 优先级最高：导入失败——此时其余校验无意义
    imp = res.get("import")
    if imp and imp.status == "fail":
        f = imp.findings[0] if imp.findings else None
        return FailureReport(FailureClass.ImportError, 0, {"message": f.message if f else ""})
    # 测试失败：按错误形状细分类别
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
    # 类型错误
    mypy = res.get("mypy")
    if mypy and mypy.status == "fail":
        f = mypy.findings[0] if mypy.findings else None
        return FailureReport(FailureClass.TypeError, 5, {"message": f.message if f else ""})
    # Lint 阻断
    ruff = res.get("ruff")
    if ruff and ruff.status == "fail":
        f = ruff.findings[0] if ruff.findings else None
        return FailureReport(FailureClass.LintBlocker, 6, {"code": f.code if f else ""})
    return FailureReport(FailureClass.Pass, 99, {})
