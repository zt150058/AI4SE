from coding_harness.clock import SystemClock, FrozenClock

def test_system_clock_increases():
    c = SystemClock()
    a, b = c.now(), c.now()
    assert b >= a

def test_frozen_clock_stable_and_advanceable():
    c = FrozenClock(t=100.0)
    assert c.now() == 100.0
    c.advance(5.0)
    assert c.now() == 105.0
