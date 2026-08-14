"""校验器层：导入/测试/lint/类型四类校验器，对工作树产出结构化结果。

每个校验器 .run() 返回 ValidatorResult（validator 名 + ok/fail + findings 列表）。
所有子进程经 _run() 统一捕获，shell=True、120s 超时；输出在落 Finding 前
经 redact 擦除密钥。裸命令（python/pytest/ruff/mypy）在 Docker 镜像内才在
PATH 上可解析——这是 run-boundary 的设计要点。
"""
import json
import subprocess
from pathlib import Path
from coding_harness.models import Finding, ValidatorResult
from coding_harness.redactor import redact

def _run(cmd, cwd):
    """统一执行子命令：返回 (returncode, redacted_stdout, redacted_stderr)。"""
    p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=120)
    return p.returncode, redact(p.stdout), redact(p.stderr)

class ImportValidator:
    """导入校验器：`python -c 'import <module>'` 验证包可导入。"""
    def run(self, worktree: Path, module: str) -> ValidatorResult:
        rc, out, err = _run(f"python -c 'import {module}'", worktree)
        if rc == 0:
            return ValidatorResult("import", "ok", [])
        return ValidatorResult("import", "fail", [Finding(str(worktree), 0, "ImportError", err.strip()[:200], "")])

class TestValidator:
    """测试校验器：运行 pytest 目标测试并解析断言/错误行。"""
    def run(self, worktree: Path, target_test: str) -> ValidatorResult:
        rc, out, err = _run(f"pytest {target_test} --tb=short -q", worktree)
        findings = []
        for line in out.splitlines():
            if "assert" in line.lower() or "Error" in line:
                findings.append(Finding(target_test, 0, "AssertionError", line.strip()[:200], ""))
        return ValidatorResult("pytest", "ok" if rc == 0 else "fail", findings)

class LintValidator:
    """Lint 校验器：ruff check，仅 E/F 级代码视为阻断性。"""
    BLOCKING = ("E", "F")
    def run(self, worktree: Path) -> ValidatorResult:
        rc, out, _ = _run("ruff check . --output-format=json", worktree)
        findings = []
        try:
            rows = json.loads(out or "[]")
            for row in rows:
                code = row.get("code", "")
                if code[:1] in self.BLOCKING:
                    findings.append(Finding(row.get("filename",""), row.get("location",{}).get("row",0),
                                           code, row.get("message",""), ""))
        except json.JSONDecodeError:
            pass
        return ValidatorResult("ruff", "ok" if not findings else "fail", findings)

class TypeValidator:
    """类型校验器：mypy，按 error: 行解析类型错误。"""
    def run(self, worktree: Path) -> ValidatorResult:
        rc, out, _ = _run("mypy . --no-error-summary", worktree)
        findings = []
        for line in out.splitlines():
            if ": " in line and "error:" in line:
                parts = line.split(":")
                line_no = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                findings.append(Finding(parts[0], line_no, "TypeError", line.strip()[:200], ""))
        return ValidatorResult("mypy", "ok" if rc == 0 else "fail", findings)
