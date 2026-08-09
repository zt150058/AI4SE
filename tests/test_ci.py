# tests/test_ci.py
import yaml
from pathlib import Path


def _ci():
    p = Path(".github/workflows/ci.yml")
    return yaml.safe_load(p.read_text(encoding="utf-8"))["jobs"]


def test_ci_has_both_jobs():
    jobs = _ci()
    assert "unit-test" in jobs
    assert "build-image" in jobs


def test_ci_unit_test_runs_on_all_events():
    # unit-test has no `if` gate → runs on every push + PR (catches Dockerfile
    # regressions early via test_docker, which builds + runs the image).
    jobs = _ci()
    assert "if" not in jobs["unit-test"]


def test_ci_build_image_gated_to_main():
    jobs = _ci()
    assert jobs["build-image"].get("if") == "github.ref == 'refs/heads/main'"


def test_ci_build_image_permissions():
    jobs = _ci()
    perms = jobs["build-image"].get("permissions", {})
    assert perms.get("contents") == "write"
    assert perms.get("packages") == "write"


def test_ci_build_image_uses_build_push_and_release():
    jobs = _ci()
    steps = jobs["build-image"]["steps"]
    uses = [s.get("uses", "") for s in steps if "uses" in s]
    assert any(u.startswith("docker/build-push-action") for u in uses)
    assert any(u.startswith("softprops/action-gh-release") for u in uses)
