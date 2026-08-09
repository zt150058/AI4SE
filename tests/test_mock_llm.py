from coding_harness.mock_llm import MockLLM
from coding_harness.models import Action, ActionType

def test_mock_returns_scripted_actions_in_order():
    a1 = Action(ActionType.edit_file, "cart.py", "fix1", ".")
    a2 = Action(ActionType.edit_file, "cart.py", "fix2", ".")
    llm = MockLLM(script=[a1, a2])
    r1 = llm.complete(messages=[], tools=[])
    r2 = llm.complete(messages=[], tools=[])
    assert r1.tool_call == a1
    assert r2.tool_call == a2
    assert r1.tokens_used > 0

def test_mock_none_means_text_only():
    llm = MockLLM(script=[None])
    r = llm.complete(messages=[], tools=[])
    assert r.tool_call is None
    assert r.text != ""
