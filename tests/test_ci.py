# tests/test_ci.py
import pytest
import yaml
from pathlib import Path

_CI_YML = Path(".github/workflows/ci.yml")

# test_ci verifies the repo's GitHub Actions workflow — a repo-context concern.
# The product Docker image ships no .github/ (it's a CLI, not a repo snapshot),
# so this suite skips in-image and runs where the repo is checked out
# (CI host + dev). Mirrors test_docker skipping when docker is absent.
pytestmark = pytest.mark.skipif(
    not _CI_YML.exists(),
    reason=".github/workflows/ci.yml not present in this context (product image ships no .github/)",
)


def _ci():
    return yaml.safe_load(_CI_YML.read_text(encoding="utf-8"))["jobs"]


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
