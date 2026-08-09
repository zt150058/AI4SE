# Coding Agent Harness

## 项目简介

Coding Agent Harness 是一个自实现的编码代理（Coding Agent）运行框架。Agent = LLM + Harness，其中 Harness 内核完全自实现，不寄生在 LangChain / AutoGen / CrewAI / LlamaIndex 等代理框架之上——仅依赖底层的 chat-completion 与 tool-call 原语。本项目的主要贡献在于**确定性反馈回路（deterministic feedback loop）**：validators -> classifier -> CorrectionLoop 状态机，代理提出编辑、运行校验器、对失败分类、注入反馈并重试，在 Pass / 预算耗尽 / 卡死循环 / 无动作四种停机条件下终止。本项目仅以 CLI 方式分发（无 WebUI / FastAPI / 云端部署；`is_deployed: false`）。

## 安装

```bash
pip install -r requirements.txt
```

Python 版本要求：3.12。

核心依赖：

- `typer` — CLI 框架
- `rich` — 终端渲染
- `keyring` — 凭据安全存储
- `pyyaml` — 配置文件解析
- `pytest` — 测试框架
- `ruff` — 代码检查与格式化
- `mypy` — 静态类型检查
- `anthropic` — LLM API 客户端

> **注意：** 需要固定 `click==8.1.7`（typer 0.12.5 兼容性要求）。

## 运行

入口点为 `python -m coding_harness`：

```bash
# 列出所有子命令
python -m coding_harness --help

# 运行修正回路（对失败测试执行反馈循环）
python -m coding_harness run --repo <repo> --test <target_test>

# 运行 Harness 测试套件
python -m coding_harness test

# 管理 ANTHROPIC_API_KEY
python -m coding_harness credential set
python -m coding_harness credential show
python -m coding_harness credential clear
```

机制演示（三场景：guardrail 拦截、feedback 改变 action、stuck-loop 停止）：

```bash
python -c "from coding_harness.demo import demo_mechanisms; import pprint; pprint.pprint(demo_mechanisms())"
```

> **说明：** AnthropicLLM 真实适配器按计划延后实现（`is_deployed: false`），当前 `run` 命令使用 MockLLM（占位实现）；可运行的演示入口为 `demo.py` 的 `demo_mechanisms()`。

## 分发（Docker + GitHub Release）

```bash
# 构建镜像
docker build -t coding-harness .

# 运行测试（镜像内 validators 的裸命令在 PATH 上可解析）
docker run --rm coding-harness test
```

CI（`.github/workflows/ci.yml`）在 main 分支推送时自动构建镜像，推送至 GHCR（`ghcr.io/<owner>/coding-harness:<sha>`），并创建 GitHub Release 附带镜像摘要。

`deploy_release_url`（占位，勿替换为真实 owner/repo）：`https://github.com/<owner>/<repo>/releases/tag/v-<sha>`

`is_deployed: false`。平台：linux/amd64。

## 安全边界

- `ANTHROPIC_API_KEY`（形状 `sk-ant-…`）**绝不**出现在源码、git 历史、镜像或日志中。
- `Redactor` 从每个 ToolResult / Event 的 payload 中擦除 `sk-ant-`。
- `CredentialStore.status()` 与 `credential show` 仅显示掩码形式 `****<last4>`（绝不显示明文）。
- `.gitignore` 与 `.dockerignore` 排除 `.env` / `*.key`。
- 密钥通过运行时环境变量注入（`-e ANTHROPIC_API_KEY`），**绝不**烘焙进镜像。
- `path_guard` + `command_guard` 对工具作用域进行围栏（Allow / Deny / RequireApproval）。
- HITL `ApprovalGateway` 在风险操作时暂停等待人工确认；非交互模式下默认拒绝。
- `tests/test_no_secrets.py` + `.pre-commit-config.yaml` 在提交时扫描真实形状密钥。

## 目录结构

```
src/coding_harness/
  models.py              # 数据类 / 枚举
  clock.py               # 时钟抽象
  redactor.py            # 密钥擦除
  event_log.py           # 事件日志
  config.py              # 配置加载
  credential_store.py    # 凭据安全存储
  llm_port.py            # LLM 端口接口
  mock_llm.py            # MockLLM 确定性实现
  governance.py          # 路径/命令守卫
  tools.py               # 工具定义
  approval_gateway.py    # 审批网关
  hitl.py                # 人在回路
  tool_dispatcher.py     # 工具分发
  validators.py          # 校验器
  classifier.py          # 失败分类器
  validator_pipeline.py  # 校验器流水线
  correction_loop.py     # 深层反馈状态机（核心贡献）
  memory_store.py        # 记忆存储
  worktree.py            # 工作树隔离
  agent_loop.py          # 外层状态机
  cli.py                 # CLI 入口
  cli_renderer.py        # CLI 渲染
  demo.py                # 机制演示
  __main__.py            # 包入口

tests/                   # 每模块一个测试文件

fixtures/cart_repo/      # 反馈回路 off-by-one 夹具仓库

Dockerfile
.dockerignore
.github/workflows/ci.yml
.pre-commit-config.yaml
requirements.txt
Makefile
pyproject.toml
config.example.yaml
```