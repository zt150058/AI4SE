import json
import subprocess
from pathlib import Path
from coding_harness.models import Finding, ValidatorResult
from coding_harness.redactor import redact

def _run(cmd, cwd):
    p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=120)
    return p.returncode, redact(p.stdout), redact(p.stderr)

class ImportValidator:
    def run(self, worktree: Path, module: str) -> ValidatorResult:
        rc, out, err = _run(f"python -c 'import {module}'", worktree)
        if rc == 0:
            return ValidatorResult("import", "ok", [])
        return ValidatorResult("import", "fail", [Finding(str(worktree), 0, "ImportError", err.strip()[:200], "")])

class TestValidator:
    def run(self, worktree: Path, target_test: str) -> ValidatorResult:
        rc, out, err = _run(f"pytest {target_test} --tb=short -q", worktree)
        findings = []
        for line in out.splitlines():
            if "assert" in line.lower() or "Error" in line:
                findings.append(Finding(target_test, 0, "AssertionError", line.strip()[:200], ""))
        return ValidatorResult("pytest", "ok" if rc == 0 else "fail", findings)

class LintValidator:
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
    def run(self, worktree: Path) -> ValidatorResult:
        rc, out, _ = _run("mypy . --no-error-summary", worktree)
        findings = []
        for line in out.splitlines():
            if ": " in line and "error:" in line:
                parts = line.split(":")
                line_no = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                findings.append(Finding(parts[0], line_no, "TypeError", line.strip()[:200], ""))
        return ValidatorResult("mypy", "ok" if rc == 0 else "fail", findings)
