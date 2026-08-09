# tests/test_ci.py
import yaml
from pathlib import Path

def test_ci_has_unit_test_job():
    p = Path(".github/workflows/ci.yml")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    jobs = data["jobs"]
    assert "unit-test" in jobs
    assert "build-image" in jobs
