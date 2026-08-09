# tests/test_demo.py
from coding_harness.demo import demo_mechanisms

def test_demo_three_scenes():
    report = demo_mechanisms()
    assert set(report.keys()) == {"guardrail_intercept", "feedback_changes_action", "stuck_loop_stop"}
    assert report["guardrail_intercept"]["denied"] is True
    assert report["feedback_changes_action"]["changed"] is True
    assert report["stuck_loop_stop"]["stopped"] is True
