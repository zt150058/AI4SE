# Coding Agent Harness — Design (SPEC)
  
---

## 1. 问题陈述

**要解决什么问题**：当 LLM 能完成大部分"思考"时，工程师的真正价值落在 harness 这层工程——治理、反馈、上下文、安全、分发。本项目交付一个**自己编码实现的 coding agent harness 内核**：把一个只会产生下一步设想的 LLM，封装成一台能稳定、可靠地在真实代码仓库中"读代码→改代码→跑测试→自我修正"的系统，并用确定性代码落实反馈闭环与治理护栏，而非依赖提示词。

**目标用户**：

- 课程助教与评审者（用 mock-LLM 单测与机制演示判定工程深度）。
- 想在本地复现一个最小可信 coding agent 的开发者（Docker 一键运行）。
- 作者本人（作为 PM/架构师/reviewer，借此形成对 Superpowers 方法论的第一手批判性理解）。

**为什么值得做**：它把"Agent = LLM + Harness"这一命题落到可验证的代码上。核心命题是——移除真实 LLM 这一不确定因素后，仓库里还剩多少可独立验证的工程？剩得多，才说明确实实现了一个 harness，而非为一个现成 LLM 编写若干提示词。

---

## 2. 用户故事（INVEST）

1. **作为评审者**，我想用 mock/stub LLM 离线、确定性地运行 harness 核心机制的单测，以便不依赖网络与真实供应商即可判定机制是否由代码实现。（Independent / Valuable / Testable）
2. **作为开发者**，我想在本地 clone 仓库后用单条 `docker build` + `docker run` 启动 harness 并通过 CLI 运行，以便零配置复现运行环境。（Negotiable / Testable）
3. **作为评审者**，我想通过 CLI 实时查看 agent 的每一步动作、反馈分类和 token 消耗，以便理解一次修复运行的全过程。（Estimable / Testable）
4. **作为 agent 自身**，我想在每次编辑后获得结构化的客观反馈（测试/导入/lint/类型）与失败分类，并据此改变下一步动作，以便多轮自我修正直到测试通过或预算耗尽。（Valuable / Testable）
5. **作为开发者**，我想让危险动作（删除、网络、越界路径）被代码护栏拦截并暂停，在交互式 CLI 中等待我批准或拒绝（非交互模式下默认拒绝、超时自动拒绝），以便 agent 不会在我离开时执行破坏性操作。（Independent / Testable）
6. **作为评审者**，我想看到一个机制演示脚本，在 mock LLM 下确定性地复现：护栏拦截、反馈闭环改变下一步、循环检测停机，以便快速核验 §A.6 的三项要求。（Testable / Small）

---

## 3. 功能规约（按模块）

### 3.1 AgentLoop（主循环，必须自实现）

- **输入**：`RunRequest(repo_path, target_test, config)`。
- **行为**：组织上下文 → 调用 `LLMPort` → 解析动作 `Action` → 交 `ToolDispatcher` 分发 → 回灌 `ToolResult` → 交 `CorrectionLoop` 验证 → 停机判断。
- **输出**：`Run{status, iters_used, tokens_used, events}`。
- **边界**：不得寄生现成 agent 框架的高层循环（LangChain `AgentExecutor`/AutoGen/CrewAI/LlamaIndex agent 等）；允许使用 LLM 单次对话补全 API、HTTP 库、解析库。
- **错误处理**：LLM/网络错误按退避重试（可配置次数），超出则 `RunStatus.ERRORED` + 停机；无无限重试。

### 3.2 CorrectionLoop（反馈闭环，重点维度）

- **输入**：每次编辑后的 worktree 状态 + `MockLLM`/真实 LLM。
- **行为**：`EDIT_APPLIED → VALIDATING → classify → (DONE | BUDGET_HIT | FEEDBACK_PREPARED → RETRY)`。
- **输出**：结构化 `FailureReport{class, priority, payload}` 与事件序列。
- **边界**：分类器为纯函数；验证器为确定性解析器（非 LLM 调用）；整环可用 mock LLM + 预置/夹具验证器离线单测。
- **停机**：`Pass` / 预算耗尽 / 连续 N 次相同失败（循环检测）。

### 3.3 ToolDispatcher + 护栏（治理）

- **输入**：`Action`。
- **行为**：先 `path_guard`（worktree 内）→ 再 `command_guard`（`Allow|Deny|RequireApproval`）→ 通过则分发到注册工具；`RequireApproval` 转 HITL。
- **输出**：`ToolResult{ok, stdout, stderr, exit_code, redacted}`。
- **边界**：护栏为确定性函数，可传构造的 `Action` 单测；危险模式来自配置（数据驱动），决策逻辑为代码。

### 3.4 HITL 状态机（治理）

- **输入**：`RequireApproval` 决策 + `ApprovalGateway`。
- **行为**：`RUN_RUNNING → RUN_PAUSED`（持久化 checkpoint + pending Approval）→ `approved`（恢复分发）| `denied`（注入"action denied"反馈）| `timeout`（超时自动拒绝）。
- **输出**：`Approval{status}` + 恢复后的运行。
- **边界**：`ApprovalGateway` 为端口。生产实现 `ConsoleApprovalGateway`：交互模式下在终端等待用户 approve/deny；非交互模式（无 TTY / CI）遇 `RequireApproval` 默认拒绝；测试注入 `ScriptedApprovalGateway`。无需 WebUI/浏览器。

### 3.5 ValidatorPipeline + 失败分类（反馈子系统）

- **输入**：worktree。
- **行为**：`Import → Test → Lint → Type`（导入/语法错误短路）。各解析器产生 `ValidatorResult`；`classify` 映射为封闭枚举 + 优先级载荷。
- **输出**：`FailureReport`。
- **边界**：lint 仅 `E/F` 阻塞、忽略样式 `D/W`；分类空间封闭（见 §6）。

### 3.6 Memory（自实现存储与检索）

- **输入**：`(task, current_failure_class)`。
- **行为**：按需检索项目约定、历史决策（failure-class → 有效修复模式）、代码库事实（模块图）。
- **输出**：紧凑上下文块。
- **边界**：存储与检索均为自有代码（JSON/SQLite），不得接用框架自带 memory；不全量载入。

### 3.7 CredentialStore + Redactor（凭据安全）

- **输入**：环境变量 / OS 钥匙串。
- **行为**：首运行引导录入（隐藏输入）；查看只回显 `****last4`；可更新/清除；`Redactor` 从所有日志/事件/`ToolResult` 中 scrub `sk-ant-*`。
- **输出**：脱敏后的可安全回灌/记录的内容。
- **边界**：key 不进源码/git/日志/shell history。

### 3.8 CLI 层（观察 + 审批，无 Web）

- **输入**：`EventLog` 事件流 + `ApprovalGateway`（交互式终端）。
- **行为**：在终端结构化输出 agent 每步动作、反馈分类、token 消耗；将事件同时写入 JSONL `EventLog`（append-only，调试与 `AGENT_LOG.md` 事实源）；遇 `RequireApproval` 时在交互式终端等待用户 approve/deny。
- **输出**：终端结构化时间线 + JSONL 事件文件 + 审批回执。
- **边界**：仅消费 `EventLog` + 经 `ApprovalGateway` 发布审批；内核对终端 I/O 无强耦合（通过端口注入）；无 HTTP/无服务器/无 WebUI。

---

## 4. 非功能性需求

- **性能**：单次修复运行在 mock LLM 下秒级完成；真实 LLM 下受供应商延迟主导。预算软上限（token/迭代）可配置。
- **安全（含凭据威胁模型）**：见 §7。
- **可用性**：单条 `docker build` + `docker run` 启动并经 CLI 运行；失败不静默崩溃（工具失败转反馈）。
- **可观测性**：终端结构化输出 + JSONL `EventLog`（append-only）为单一观测/检查点/调试事实源；每步事件带标签联合，终端与 `AGENT_LOG.md` 均消费之；不依赖 WebUI。

---

## 5. 系统架构

依赖方向向内：循环与机制依赖端口（抽象接口），不依赖具体 LLM/工具/CLI 实现。由此可注入 mock LLM 离线单测每个机制。

```
                         ┌─────────────────────────────────────────┐
                         │              config (declarative)        │
                         │ (scope rules, danger patterns, budget)   │
                         └────────────────┬────────────────────────┘
                                          │ governs
   ┌──────────────┐   actions    ┌────────▼─────────┐   events    ┌──────────────┐
   │  LLM port    │◄────────────►│   KERNEL CORE    │────────────►│  event log    │
   │ (real/mock)  │  completions │  (no framework)   │ append-only │ JSONL (ckpt)  │
   └──────────────┘              └────────┬─────────┘             └──────┬───────┘
            ▲                             │ dispatch                    │ consume
            │                             ▼                             ▼
   ┌────────┴──────┐  tool I/O   ┌──────────────────┐  approve   ┌──────────────┐
   │ tool registry │◄────────────►│ tool dispatcher  │◄──────────►│  CLI layer    │
   │ file/shell/   │             │ + scope-fence +  │  deny/tty  │ ConsoleApproval│
   │ test runner   │             │  guardrail(HITL) │            │ Gateway       │
   └───────────────┘             └────────┬─────────┘            └──────────────┘
            ▲                             │ runs
            │                             ▼
   ┌────────┴──────────────────────────────────────┐
   │  FEEDBACK SUBSYSTEM (deep dimension)          │
   │  validators (pytest/import/ruff/mypy parsers) │
   │  → failure classifier → structured feedback   │
   │  → correction-loop state machine              │
   └───────────────────────────────────────────────┘
            ▲ cross-session
   ┌────────┴──────┐
   │   memory      │ (self-built store+retrieve)
   │  + retrieve   │
   └───────────────┘
```

**内核组件（必须自实现）**：`AgentLoop`（外层任务循环）、`CorrectionLoop`（内层反馈状态机）、`ToolDispatcher`（路由 + scope-fence + guardrail）、`EventLog`（append-only）。

**端口（可替换）**：`LLMPort`（真实 Anthropic / `MockLLM`）、`ToolPort` 实现（文件/shell/test-runner）、`CredentialStore`（keyring 实现）、`ApprovalGateway`（生产实现 `ConsoleApprovalGateway` / 测试 `ScriptedApprovalGateway`）、`MemoryStore`。

**外部依赖**：LLM 供应商 Anthropic；外部工具 git / pytest / ruff / mypy（均进 Docker 镜像）。

**数据流（端到端，一次修复运行）**：

1. config 加载 → 凭据从 keyring 取（不记日志）→ worktree 创建于 `./agent-workspace/<run-id>`（路径围栏生效）。
2. 外层循环：构建上下文（系统提示 + MemoryStore 仓库事实 + 失败测试源）→ 调 `LLMPort` → 解析 `Action(edit_file, ...)` → 分发：`path_guard ✓`、`command_guard n/a` → 应用编辑 → 交 CorrectionLoop。
3. CorrectionLoop：`VALIDATING` 跑 pipeline（Import ✓、Test ✗ AssertionError @ cart.py:42、Lint ✓、Type ✓）→ `classify → FailureReport(AssertionFailure, line=42, snippet)` → 非停机 → `FEEDBACK_PREP`（结构化反馈 + 记忆"off-by-one"）→ `RETRY`（追加反馈 → 调 LLM → 下一个编辑）→ 第 3 轮 `classify=Pass → DONE`。
4. 外层停机（测试绿）→ `RunStatus.SUCCEEDED`。
5. 全程每步追加 `Event`：`StepStarted/ActionProposed/GuardDecision/EditApplied/ValidatorResult/FailureClassified/ApprovalRequested/ApprovalReceived/LoopIterated/RunFinished/TokenBudgetTick`。

**HITL 协调**：循环在单 async 任务中等待 LLM/工具；遇 `RequireApproval` 时在 `ApprovalReceived` 事件上 `await`（或轮询网关）。交互式运行下 `ConsoleApprovalGateway` 在终端阻塞等待用户输入；非交互式（无 TTY/CI）默认拒绝；超时由配置自动拒绝——三者均保持可测、有界。

---

## 6. 数据模型

核心实体（带标签/结构化，非字符串化）：

- `Action{type: edit_file|run_shell|run_tests|read_file, target, payload, cwd}` — 护栏检查单元。
- `ToolResult{ok: bool, stdout, stderr, exit_code, redacted}` — stdout 经 Redactor scrub。
- `ValidatorResult{validator, status, findings[]}`；`Finding{file, line, code, message, snippet}`。
- `FailureReport{class: FailureClass, priority, payload}` — 分类器输出。
- `Event{seq, run_id, type, ts, payload}` — 带标签联合；`ts` 由 clock 端口注入（测试可冻结时间）。
- `Run{id, status, repo, target_test, started_at, iters_used, tokens_used}`。
- `Approval{id, run_id, action, reason, preview, status: pending|approved|denied|timeout}`。
- `MemoryRecord{repo, kind, key, value, last_used}`。

**FailureClass（封闭枚举）**：`ImportError | SyntaxError | NameError | AttributeError | AssertionFailure | CollectionError | Timeout | LintBlocker | TypeError | ParseError | Pass`。优先级：Import > Syntax > Collection > NameError > Assertion > TypeError > LintBlocker（仅 `E/F`，忽略样式 `D/W`）。每轮只向模型展示当前最高优先级失败，避免淹没。

---

## 7. 凭据与分发设计

### 7.1 凭据威胁模型与对策（§3.1）

| 威胁 | 对策 |
|---|---|
| Key 进源码/git | `.gitignore` 排除 `.env`；pre-commit 扫描 `sk-ant-` 模式；key 永不作默认参数 |
| Key 进 shell history | 不用 CLI `export`；运行时经 `python-dotenv` 从 `.env` 加载（仅 fallback） |
| Key 进日志/LLM 上下文 | `Redactor`（纯函数，单测）scrub `sk-ant-*`，作用于所有 `ToolResult`/`Event` payload |
| 明文 `.env` 风险 | 文档说明；keyring 为**主**存储，`.env` 为 fallback 并打印警告 |
| 轮换/吊销 | CLI `harness credential set/show/clear`；`show` 只回显 `****last4` |

**流程**：首运行 `harness credential set`（隐藏 `getpass` 输入）→ 存入 OS keyring（Windows Credential Manager）。`CredentialStore` 为端口；测试用内存 fake。

### 7.2 分发：CLI-only + Docker + GitHub Release（唯一分发路径）

**设计目标**：项目为 CLI-only（无 WebUI、无后台服务器、无云托管）。Docker 是唯一可复现运行环境与唯一分发产物；镜像发布到公开容器仓库（GHCR），并创建对应的版本化 GitHub Release 作为获取入口。无 PyPI/包管理分发，无第二条构建路径——本地、CI、Release 三者同一 Dockerfile。本项目不提供公网部署地址（`is_deployed: false`），交付物以固定版本的 GitHub Release 页面链接（`deploy_release_url`）为准。

**本地 / 可复现运行**：

```bash
git clone <repo> && cd <repo>
docker build -t coding-harness .
docker run --rm -e ANTHROPIC_API_KEY=$KEY -v "$(pwd)/workspace:/workspace" coding-harness run --repo /workspace/<repo> --test <target_test>
# agent 在容器内 CLI 运行；事件输出到终端并写 JSONL EventLog
```

**分发产物（GHCR + GitHub Release）**：

- **镜像地址**：`ghcr.io/<owner>/coding-harness:<version>`（CI `build-image` job 构建并推送；`<version>` 同时打 `latest` + git tag + 镜像 digest）。
- **Release 链接**：`https://github.com/<owner>/<repo>/releases/tag/v<version>`（版本化 GitHub Release，作为获取入口；非公网服务地址）。
- **Release 页面内容（必需字段）**：
  - Docker 镜像地址：`ghcr.io/<owner>/coding-harness:<version>`（附 digest）。
  - `docker pull` 命令：`docker pull ghcr.io/<owner>/coding-harness:<version>`。
  - 完整 CLI 运行命令（含 `-e ANTHROPIC_API_KEY`、挂载卷、`run` 子命令与参数）。
  - 版本号或镜像 digest。
  - API Key 安全配置方式（见 §7.1：仅运行时 `-e` 注入，不进镜像/不进仓库）。
  - 支持的平台、架构与已知限制（见下文）。
- **跨产物一致性**：Release 关联的镜像即 CI 推送到 GHCR 的同一镜像——`docker pull` 得到的与本地 `docker build` 等价，cloud==local==CI 产物。

**Dockerfile（设计，未写代码）**：

1. Base：`python:3.12-slim`（pinned）。
2. 系统依赖：仅 `git`（worktree 管理）。
3. Python 依赖：先拷 lockfile，`pip install --no-cache-dir`（先于源码分层）。
4. 源码：harness 包 + 测试 + 夹具仓库（使 `docker run coding-harness test` 在镜像内可用）。
5. 非 root 用户 `appuser`（最小权限）。
6. Entrypoint：`python -m coding_harness`（CLI 入口）；`CMD` 默认打印帮助，子命令 `run`/`test`/`credential` 透传。
7. 无 `EXPOSE`、无端口映射、无 `HEALTHCHECK`（CLI 项目无网络服务）。

**密钥硬规则（结构性强制）**：

- 镜像内零 `ANTHROPIC_API_KEY` 引用；无 `ARG` 透出 key（build-arg 进 `docker history`）。构建天然无密钥 → 可安全推 GHCR / 检视。
- `.dockerignore` 排除 `.env`、`.env.*`、`**/*.key`、本地 keyring、`.git/`、`__pycache__`、`agent-workspace/`。
- 运行时注入：仅 `-e ANTHROPIC_API_KEY=$KEY`（或经 keyring，见 §7.1）；不存云端 secret、无云部署。
- `Redactor` 保证日志/事件/`ToolResult` 不泄 `sk-ant-*`；`--rm` 销毁 env。

**README 分发章节**（仅 Docker + GitHub Release）：

- 前置：Docker。
- 获取方式二选一：① `docker pull ghcr.io/<owner>/coding-harness:<version>`；② clone 仓库后 `docker build`。
- 运行命令（CLI，含 key 的 `-e` 注入与卷挂载）。
- Release 页面链接与字段说明。
- 已知限制：linux/amd64 镜像（若构建多架构则注明）；CLI 非交互模式下 `RequireApproval` 默认拒绝；需有效 Anthropic key；worktree 每次运行临时。

**移除**：PyPI / `pip install` 分发；Fly.io / Render / 云主机 / 公网 URL / 云端 Secret / 云部署 deploy job；WebUI / FastAPI / SSE / HTTP 审批接口 / 端口暴露。

---

## 8. 技术选型与理由

- **语言：Python**。pytest + asyncio 做 TDD 最顺；LLM SDK 生态成熟；mock-LLM 即 stub 类，确定性测试最简；`keyring` 跨平台凭据；Docker 分发顺手；交互式 CLI（`typer`/`rich` 或等价）做终端观察与审批轻量。迭代快、可读性高，最宜展示 harness 内部。
- **LLM 供应商：Anthropic Claude**（真实路径）。你在 Claude 生态；SDK 成熟、tool-use 原生。抽象层只对接 chat-completion + tool-call 两原语；mock 路径供应商无关。
- **分发：CLI-only + Docker（唯一）+ GitHub Release**。可复现、单一产物；Release 链接作为获取入口；不提供公网部署地址（`is_deployed: false`）。
- **无 Web/无服务器**：纯 CLI 项目，豁免 Open Design 强制要求（§3.6 条件项）；不引入 FastAPI / WebUI / SSE / 后台服务。
- **CI/CD**：GitHub Actions（`.github/workflows/ci.yml`），含 `unit-test`（必需名）job 与 `build-image`（推 GHCR + 发 Release）。

---

## 9. 领域与机制设计（A 文件额外要求，呼应 §A.4）

**领域：coding（软件开发）。** 其反馈信号、危险动作、所需工具、记忆需求均有最清晰、最可编码、最难用提示词规避的形态。

- **动作/工具**：读写文件、执行 shell、运行构建与测试。落在 `ToolDispatcher` + 注册工具。
- **客观反馈信号**：运行测试（pytest）/ lint（ruff）/ 类型（mypy）/ 导入语法检查——客观、确定、可回灌。落实为**自编写的校验器/传感器**（解析产物 → 客观判定 → 回灌循环），而非"让 LLM 自行检查"的提示词。
- **危险动作**：删除数据库/危险 shell/对外发布/越界路径。落实为**自编写的护栏**（识别 → 拦截 → HITL），而非"提醒注意安全"的提示词。
- **记忆**：跨会话记项目约定、历史决策、代码库知识；存储与检索自实现，不全量载入。

**重点维度：反馈闭环**（§A.4-D 主要贡献）。理由：coding agent 最核心、最"像代码"的能力；与治理天然组合；分类器为纯函数、整环可 mock LLM 离线确定性单测，最契合 §A.4(C) 硬判据。治理（护栏/沙箱/HITL 状态机/范围围栏）作为可运行最低实现并列支撑。

**机制如何编码实现（呼应 §A.4-B/C）**：

- 反馈信号 = `ValidatorPipeline` + `classify` 纯函数。
- 危险动作拦截 = `command_guard`/`path_guard` 纯函数。
- HITL = async pause/resume 状态机，`ApprovalGateway` 端口可注入 stub。
- 停机 = 代码判定（Pass / 预算 / 循环检测 N 次相同失败）。
- 移除真实 LLM 后，以上每个机制均可用 mock/stub LLM + 夹具仓库/预置 pipeline 结果确定性单测——配置文件/规则文件/提示词文件均属"内容物"，不计入 harness 实现工作量。

---

## 10. 验收标准

- **机制单测（mock LLM，离线，确定性）全部通过**：护栏拦截 `rm -rf`、scope-fence 拒越界路径、分类器产出正确 `FailureClass`、CorrectionLoop 绿则 DONE、失败-重试-通过事件序列精确、循环检测停机、HITL approve 恢复、HITL 超时自动拒绝、Redactor scrub key。
- **集成测试**：夹具仓库 + 真实验证器 + mock LLM 提供修复，端到端绿运行。
- **机制演示**：`demo_mechanisms.py` 在 mock LLM 下确定性复现 ① 护栏拦截危险动作；② 注入失败→反馈闭环改变下一步；③ 循环检测停机。
- **分发**：CLI 可运行（`docker run ... coding-harness run ...`）；Docker 镜像可从公开 registry 拉取（`docker pull ghcr.io/<owner>/coding-harness:<version>`）；GitHub Release 页面可访问（`https://github.com/<owner>/<repo>/releases/tag/v<version>`）；Release 中的命令能在全新机器上复现运行；`docker run coding-harness test` 在镜像内跑通 mock-LLM 单测与机制演示。**不要求**公网 URL、WebUI 或云端 deploy 成功（`is_deployed: false`，以 `deploy_release_url` Release 链接为交付）。
- **凭据**：`grep -r sk-ant` 在仓库（含历史）无命中；`docker history` 无 key；日志/事件经 Redactor 无 key。
- **CI**：最后一次 pipeline 绿；`unit-test` job 存在且通过；`build-image`（推 GHCR + 发 Release）成功。
- **模块数**：≥3 个职责清晰功能模块（AgentLoop / CorrectionLoop / ToolDispatcher+Governance / Feedback / Memory / Credential / CLI 均独立）。

---

## 11. 风险与未决问题

- **规范清晰度风险**：spec 中的隐性假设可能在冷启动（§4.5 陌生智能体）暴露——如 worktree 根路径约定、事件 schema 字段、mock LLM 脚本格式。PLAN 须显式写清。
- **mock LLM 脚本化复杂度**：编辑序列脚本若写死易脆；需一个小型脚本 DSL（"第 N 轮返回某 Action"），其本身也需测试。
- **Release 产物完整性**：GHCR 镜像 digest 与 Release 页声明的 digest 不一致会误导复现；mitigation：CI 在 Release 描述中自动写入构建产出的镜像 digest，人工不手填。
- **Docker 平台兼容性**：宿主架构/平台差异（amd64 vs arm64，Windows Docker Desktop vs Linux）可能导致镜像无法运行；mitigation：明确声明目标平台（默认 linux/amd64），必要时构建多架构镜像；以容器内 Linux 为唯一真相源。
- **CLI 非交互审批风险**：CI/无 TTY 环境下遇 `RequireApproval` 若默认放行则危险，若默认拒绝则可能使 demo 流程中断；mitigation：`ConsoleApprovalGateway` 在非交互模式严格默认拒绝并注入"action denied"反馈，由 agent 改道；demo 场景设计上规避触发审批的动作。
- **lint/类型噪声**：ruff/mypy 噪声多；以"仅 `E/F` 阻塞、忽略样式"与"每轮只展示最高优先级失败"两道闸控制。
- **worktree 与 Windows 宿主**：作者主机为 Windows；Docker 内为 Linux，需确保 git worktree 行为一致；mitigation：以容器内 Linux 为唯一真相源，不在 Windows 宿主直接跑 worktree。
- **时间窗**：双层状态机 + CLI + 分发 + CI 范围适中；若吃紧，治理/HITL 保持最低实现，深度集中于反馈闭环（已对齐 §A.4-D）。

---

*本 SPEC 为 brainstorming 沉淀产物，下一步交 `writing-plans` 技能分解为实现计划。*
