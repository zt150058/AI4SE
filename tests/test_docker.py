# tests/test_docker.py
import shutil, subprocess
import pytest

@pytest.mark.skipif(shutil.which("docker") is None, reason="no docker")
def test_image_runs_tests():
    subprocess.run(["docker","build","-t","coding-harness","."], check=True)
    r = subprocess.run(["docker","run","--rm","coding-harness","test"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
