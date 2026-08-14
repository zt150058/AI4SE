# Coding Agent Harness

## 项目简介

Coding Agent Harness 是一个用 Python 自主实现的编码代理运行框架。它负责调用 LLM、执行文件和 Shell 工具、运行测试，并把失败结果反馈给代理继续修正。

项目的核心是一个可确定性测试的反馈闭环：

```text
执行修改 → 运行校验 → 分类失败 → 生成反馈 → 再次尝试
```

Harness 内核不依赖 LangChain、AutoGen、CrewAI 等现成 Agent 框架。主循环、工具分发、治理护栏、HITL 审批、记忆和反馈状态机都由本项目自行实现，并可使用 `MockLLM` 离线测试。

## 安装

要求 Python 3.12。

```bash
python -m venv .venv
pip install -r requirements.txt
```

激活虚拟环境：

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "src"
```

```bash
# Linux / macOS
source .venv/bin/activate
export PYTHONPATH=src
```

项目采用 `src/` 目录布局，因此在主机上运行前需要设置 `PYTHONPATH=src`。Docker 镜像已经自动配置该路径。

## 运行

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

运行三场景机制演示：

```bash
python -c "from coding_harness.demo import demo_mechanisms; import pprint; pprint.pprint(demo_mechanisms())"
```

演示会确定性复现以下行为：

1. 护栏拦截危险命令。
2. 一次失败被反馈给 Agent，下一步动作随之改变。
3. 重复失败达到阈值后，反馈循环自动停止。

> 当前 `run` 命令接入的是 `MockLLM`，用于验证 Harness 机制，尚未接入真实 LLM 完成代码修复。`credential` 命令当前使用环境变量后端，不会跨进程持久保存密钥。

## 分发（Docker + GitHub Release）

本项目通过 Docker 分发，目标平台为 `linux/amd64`。

```bash
# 构建镜像
docker build -t coding-harness .

# 运行测试（镜像内 validators 的裸命令在 PATH 上可解析）
docker run --rm coding-harness test
```

也可以直接拉取已经由 CI 构建的镜像：

```bash
docker pull ghcr.io/zt150058/coding-harness:latest
docker run --rm ghcr.io/zt150058/coding-harness:latest --help
```

GitHub Actions 会在 `main` 分支更新后执行单元测试、构建镜像、推送至 GHCR，并创建带镜像摘要的 [GitHub Release](https://github.com/zt150058/AI4SE/releases)。

## 安全边界

- API Key 不硬编码到源码、Git 历史或 Docker 镜像中。
- `Redactor` 会在工具结果和事件日志中隐藏符合密钥形状的内容。
- `path_guard` 限制文件操作范围，阻止访问工作区之外的路径。
- `command_guard` 对危险命令执行拒绝或要求人工审批。
- 非交互环境遇到需要审批的操作时默认拒绝。
- `.gitignore`、`.dockerignore`、测试和 pre-commit hook 共同检查凭据泄漏风险。

## 目录结构

```text
src/coding_harness/
  agent_loop.py          # Agent 外层主循环
  correction_loop.py     # 反馈闭环状态机（核心贡献）
  llm_port.py            # 可注入的 LLM 接口
  mock_llm.py            # 离线确定性 MockLLM

  tools.py               # 文件与 Shell 工具
  tool_dispatcher.py     # 工具分发
  governance.py          # 路径和命令护栏
  approval_gateway.py    # 审批接口
  hitl.py                # 人在回路状态机

  validators.py          # 测试、Lint、类型等校验器
  validator_pipeline.py  # 校验器流水线
  classifier.py          # 失败分类

  memory_store.py        # SQLite 记忆存储
  event_log.py           # JSONL 事件日志
  credential_store.py    # 凭据存储接口
  redactor.py            # 敏感信息脱敏
  cli.py                 # CLI 命令
  demo.py                # 三场景机制演示

tests/                   # 单元测试与集成测试
fixtures/cart_repo/      # 反馈闭环测试夹具
docs/                    # SPEC、PLAN、过程日志与反思报告

Dockerfile               # Docker 镜像
.github/workflows/ci.yml # GitHub Actions
requirements.txt         # Python 依赖
config.example.yaml      # 配置示例
```
