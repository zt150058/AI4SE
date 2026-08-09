from coding_harness.config import load_config

def test_load_config(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text(
        "worktree_root: ./agent-workspace\n"
        "budget_max_iterations: 6\n"
        "budget_max_tokens: 50000\n"
        "deny_patterns: ['rm -rf', 'git push --force']\n"
        "approval_patterns: ['pip install', 'git clone']\n"
        "approval_timeout_minutes: 15\n"
        "lint_codes_blocking: ['E', 'F']\n"
        "memory_store_path: ./memory.db\n"
        "llm_provider: anthropic\n"
        "llm_model: claude-sonnet-5\n"
    )
    cfg = load_config(str(p))
    assert cfg.budget_max_iterations == 6
    assert cfg.deny_patterns == ["rm -rf", "git push --force"]
    assert cfg.lint_codes_blocking == ["E", "F"]
