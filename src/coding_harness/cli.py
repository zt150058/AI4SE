"""CLI 入口：run / test / credential 三组子命令（typer）。

run 命令组装完整管线（AgentLoop+CorrectionLoop+MemoryStore+Dispatcher+HITL）
但当前用 MockLLM 占位（AnthropicLLM 延后，is_deployed:false）；test 命令派发
pytest；credential set/show/clear 管理运行时密钥（show 仅掩码显示）。
"""
import typer
from pathlib import Path
from coding_harness.config import Config, DEFAULT_CONFIG
from coding_harness.credential_store import EnvCredentialStore, mask_key

app = typer.Typer()

@app.command()
def run(repo: str, test: str, config: str = typer.Option("config.example.yaml")):
    """针对 repo + 失败测试运行修复型闭环。"""
    from coding_harness.event_log import EventLog
    from coding_harness.clock import SystemClock
    from coding_harness.mock_llm import MockLLM
    from coding_harness.tool_dispatcher import ToolDispatcher
    from coding_harness.tools import FileTool, ShellTool
    from coding_harness.hitl import HitlMachine
    from coding_harness.approval_gateway import ConsoleApprovalGateway
    from coding_harness.correction_loop import CorrectionLoop
    from coding_harness.memory_store import SQLiteMemoryStore
    from coding_harness.agent_loop import AgentLoop, RunRequest
    from coding_harness.models import ActionType
    cfg = DEFAULT_CONFIG
    log = EventLog(Path("agent-workspace/events.jsonl"), SystemClock())
    hitl = HitlMachine(log, ConsoleApprovalGateway(cfg.approval_timeout_minutes), SystemClock())
    disp = ToolDispatcher({ActionType.edit_file: FileTool(), ActionType.read_file: FileTool(),
                          ActionType.run_shell: ShellTool()}, Path(repo),
                          cfg.deny_patterns, cfg.approval_patterns, hitl, log, SystemClock())
    cl = CorrectionLoop(MockLLM([]), disp, log, SystemClock(), cfg)
    mem = SQLiteMemoryStore(cfg.memory_store_path)
    agent = AgentLoop(cl, mem, log, SystemClock(), cfg)
    import asyncio
    run_obj = asyncio.run(agent.run(RunRequest(repo=repo, target_test=test, config=cfg)))
    for e in log.events_for(run_obj.id):
        typer.echo(__import__("coding_harness.cli_renderer", fromlist=["CliRenderer"]).CliRenderer.render(e))

@app.command()
def test():
    """运行 harness 测试套件（pytest）。"""
    import subprocess
    rc = subprocess.call(["pytest", "-q"])  # 派发裸 pytest；镜像内 pytest 在 PATH 上
    raise typer.Exit(code=rc)

cred_app = typer.Typer()
app.add_typer(cred_app, name="credential")

@cred_app.command("set")
def cred_set():
    """交互式读取并写入 ANTHROPIC_API_KEY 到环境。"""
    import getpass
    EnvCredentialStore().set(getpass.getpass("ANTHROPIC_API_KEY: "))

@cred_app.command("show")
def cred_show():
    """以掩码形式（****<last4>）显示当前密钥，绝不输出明文。"""
    typer.echo(mask_key(EnvCredentialStore().get()))

@cred_app.command("clear")
def cred_clear():
    """清除环境中的 ANTHROPIC_API_KEY。"""
    EnvCredentialStore().clear()
    typer.echo("cleared")
