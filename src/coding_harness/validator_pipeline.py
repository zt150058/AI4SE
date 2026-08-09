# src/coding_harness/validator_pipeline.py
from pathlib import Path
from coding_harness.validators import ImportValidator, TestValidator, LintValidator, TypeValidator
from coding_harness.classifier import classify
from coding_harness.models import ValidatorResult, FailureReport

def run_pipeline(worktree: Path, target_test: str, module: str):
    results: list[ValidatorResult] = []
    imp = ImportValidator().run(worktree, module)
    results.append(imp)
    if imp.status == "fail":
        return results, classify(results)
    results.append(TestValidator().run(worktree, target_test))
    results.append(LintValidator().run(worktree))
    results.append(TypeValidator().run(worktree))
    return results, classify(results)
