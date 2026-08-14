"""校验器流水线：有序运行四类校验器并短路。

导入失败即短路返回（后续校验无意义）；否则依次跑 测试→lint→类型，
再交 classifier 归约为 FailureReport。
"""
from pathlib import Path
from coding_harness.validators import ImportValidator, TestValidator, LintValidator, TypeValidator
from coding_harness.classifier import classify
from coding_harness.models import ValidatorResult, FailureReport

def run_pipeline(worktree: Path, target_test: str, module: str):
    """运行校验流水线：导入先行，导入失败即短路；否则跑测试/lint/类型后分类。"""
    results: list[ValidatorResult] = []
    imp = ImportValidator().run(worktree, module)
    results.append(imp)
    if imp.status == "fail":
        return results, classify(results)  # 短路：导入失败时其余校验无意义
    results.append(TestValidator().run(worktree, target_test))
    results.append(LintValidator().run(worktree))
    results.append(TypeValidator().run(worktree))
    return results, classify(results)
