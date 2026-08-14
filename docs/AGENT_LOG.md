# AGENT_LOG — Coding Agent Harness 实现日志

> 本日志按时间顺序从 Git 提交、task report、两阶段评审记录和 `docs/SPEC_PROCESS.md` 回填。每条记录包含任务、技能/上下文、subagent 产出、人工干预与经验。详细原始报告保存在本地 `.superpowers/sdd/2026-08-09-coding-agent-harness/`；commit hash 是仓库内可复核的长期证据。

## 2026-08-01 — 规约形成

### 17:04 — Brainstorming 与 SPEC 初稿

- **技能与上下文：** `superpowers:brainstorming`；围绕 Agent = LLM + Harness、六个基础维度与一个重点维度逐段确认设计。
- **关键产出：** 确定反馈闭环为主要贡献，采用 `ValidatorPipeline → classifier → CorrectionLoop`，同时保留治理、HITL、记忆、工具和配置的最低完整实现。
- **commit：** `724f69b`。
- **人工判断：** 没有接受“把规则主要写进 prompt”的捷径，坚持反馈与危险动作必须由确定性代码实现。
- **经验：** 设计阶段最重要的不是功能数量，而是明确哪些机制在移除真实 LLM 后仍能被测试。

## 2026-08-09 — 规约收敛、计划与冷启动

### 15:15–15:40 — 范围收敛与 25-task 计划

- **技能与上下文：** `brainstorming` → `writing-plans`；每个 task 要求明确文件、接口、失败测试、GREEN 命令和 commit。
- **关键产出：** 将实现拆为 25 个 TDD task，覆盖模型、治理、反馈、记忆、编排、CLI、演示、Docker 和 CI。
- **commits：** `a6378e3`, `62a39a9`, `7056662`, `9e152fb`。
- **人工干预：** 要求计划主体改为中文，但代码、标识符和命令保持英文；发现用户故事编号被机械改写破坏后，人工复核并恢复语义。
- **经验：** 自动编辑即使语法正确也可能破坏需求语义，批量改写后必须全文复核。

### 15:55–16:22 — Task 1 冷启动验证

- **任务：** Task 1，项目脚手架、依赖、测试入口。
- **技能与上下文：** 使用不同类型的陌生 Codex session，仅提供 SPEC 与 PLAN；要求遇到歧义即停止，不得猜测。
- **RED：** 第一轮尚未执行代码就发现计划要求先运行 `make test`，但 Makefile 和依赖要到后续步骤才创建，RED 本身不可执行。
- **人工干预：** 将 Task 1 重排为“测试基础设施 bootstrap → 写失败测试 → RED → GREEN”，并补充依赖安装、Windows/Docker 边界和权威文档路径。
- **第二轮结果：** 实测 `ModuleNotFoundError: No module named 'coding_harness'`，随后最小实现达到 1 passed。
- **commits：** `d344772`, `1a30c8d`, `51221b1`。
- **经验：** 冷启动的价值不是让另一个 agent 多写代码，而是在最便宜的阶段暴露计划中不可执行的隐性前提。

## M1：Core Infrastructure（Tasks 2–7）

### 16:45 — Task 2：数据模型与枚举

- **技能与上下文：** `subagent-driven-development` + `test-driven-development`；仅提供 Task 2 brief 和接口清单。
- **TDD：** RED 为 `coding_harness.models` 不存在；GREEN 为 5 passed。
- **产出：** Action、ToolResult、Finding、ValidatorResult、FailureReport、Event、Run、Approval、MemoryRecord 及相关枚举。
- **commit：** `929c5ee`。
- **人工/评审：** 两阶段评审通过；将类型精度和换行问题记为非阻塞项。
- **经验：** 先固定跨模块数据契约，后续 subagent 才能在没有完整上下文的情况下独立工作。

### 16:50 — Task 3：时钟端口

- **TDD：** RED 为 clock 模块导入失败；GREEN 为 2 个 focused test、8 个全量测试通过。
- **产出：** `ClockPort`、`SystemClock`、`FrozenClock`。
- **commit：** `5b55e32`。
- **人工/评审：** 保留最小端口，不加入调度器或计时框架。
- **经验：** 把时间作为依赖注入，是让超时、审批和事件顺序确定性测试的前提。

### 16:53 — Task 4：Redactor

- **TDD：** RED 为 redactor 模块导入失败；GREEN 为 3 focused / 11 full passed。
- **产出：** `redact()` 与可扩展的 `SECRET_PATTERNS`。
- **commit：** `6aa2477`。
- **人工/评审：** 确认替换发生在日志和 ToolResult 进入系统边界时，而不是依赖调用者自觉。
- **经验：** 安全机制应是默认路径上的纯函数，而不是文档中的提醒。

### 16:58 — Task 5：EventLog

- **TDD：** RED 为导入失败；GREEN 为 3 focused / 14 full passed。
- **产出：** append-only JSONL、按 run 检索、checkpoint。
- **commit：** `2f56647`。
- **人工/评审：** 评审指出重新打开既有日志时 seq 会从 0 开始；因当前生命周期是每次 run 新建日志，记录为后续持久化扩展风险。
- **经验：** 评审不应只给“过/不过”，还要区分当前契约内缺陷和未来扩展风险。

### 17:03 — Task 6：配置加载器

- **TDD：** RED 为 config 模块导入失败；GREEN 为 1 focused / 15 full passed。
- **产出：** YAML 加载、默认预算、治理规则和路径配置。
- **commit：** `c414832`。
- **人工/评审：** 检查可变默认值，使用 `default_factory` 避免实例间共享状态。
- **经验：** 声明式配置必须进入确定性代码路径，否则只是内容物而不是 harness 能力。

### 17:08–17:17 — Task 7：凭据端口与掩码

- **TDD：** RED 为 credential_store 模块导入失败；GREEN 为 2 focused / 17 full passed。
- **产出：** `CredentialPort`、环境变量后端、keyring 后端和只显示尾四位的 `mask_key()`。
- **commits：** `988316f`, `854cbe8`。
- **人工干预：** 代码质量评审发现 `KeyringCredentialStore.clear()` 捕获所有异常，会掩盖权限、锁定等真实错误。人工选择只捕获 `PasswordDeleteError`，修复后重新评审通过。
- **经验：** “清除操作幂等”不能成为吞掉基础设施故障的理由；异常边界应尽可能窄。

### M1 阶段评审

- **技能：** `requesting-code-review`，先 spec 合规、再代码质量。
- **结果：** 36 tests green；M1 合并到 main，里程碑 commit `854cbe8`。
- **流程偏离：** 最初设想每个 worktree 都走远端 PR；人工随后选择本地 fast-forward 的连续集成方式完成 M2–M7，并保留完整分支、报告与评审 diff。该偏离降低了远端流程可见性，但没有跳过两阶段评审。

## M2：LLM 抽象（Task 8）

### 17:39 — Task 8：LLMPort 与 MockLLM

- **技能与上下文：** 新鲜 subagent，只提供端口签名、脚本 DSL 和离线测试要求。
- **TDD：** RED 为 mock_llm 模块不存在；GREEN 为 19 passed。
- **产出：** `LLMPort`、`LLMResponse`、按脚本顺序返回 Action/None 的 `MockLLM`。
- **commit：** `90b6447`。
- **人工/评审：** 确认脚本耗尽明确抛错，不自动循环或生成默认动作；真实供应商适配器不进入本阶段。
- **经验：** 明确、会耗尽的 mock 比“聪明”的 fake 更适合暴露循环边界错误。

## M3：Governance（Tasks 9–13）

### 17:52 — Task 9：path_guard 与 command_guard

- **TDD：** RED 为 governance 模块不存在；GREEN 为 24 passed。
- **产出：** worktree 路径围栏、Deny 优先于 RequireApproval 的命令治理。
- **commit：** `038223c`。
- **人工/评审：** 重点检查 `.resolve()` 与 `relative_to()`，确保 `..` 和绝对路径无法逃逸。
- **经验：** 安全护栏的价值来自执行前的确定性短路，而不是模型“应该不会这么做”。

### 22:13 — Task 10：FileTool 与 ShellTool

- **TDD：** 4 个新测试加入后全量 28 passed。
- **产出：** 文件读写和 shell 执行，stdout/stderr 在生成 ToolResult 前统一脱敏。
- **commit：** `39c8cff`。
- **人工/评审：** 复核两个输出流均经过 Redactor；超时处理作为非阻塞改进记录。
- **经验：** 工具边界是敏感数据最容易泄漏的位置，应在返回结果前集中处理。

### 22:21 — Task 11：ApprovalGateway

- **TDD：** 全量 30 passed。
- **产出：** `ScriptedApprovalGateway` 与 `ConsoleApprovalGateway`。
- **commit：** `9b0c04c`。
- **人工/评审：** 确认非交互环境永不默认批准。
- **经验：** 不确定运行环境下，审批系统必须 fail closed。

### 22:29 — Task 12：HITL 状态机

- **TDD：** 全量 32 passed。
- **产出：** `RUNNING → PAUSED → RUNNING`、ApprovalRequested/Received 事件与 checkpoint。
- **commit：** `a36a856`。
- **人工/评审：** 逐步追踪事件顺序，确认 checkpoint 在等待外部审批前写入。
- **经验：** HITL 不只是一个 yes/no 回调；暂停点和恢复所需事实必须先持久化。

### 22:35–22:47 — Task 13：ToolDispatcher

- **TDD：** 初版全量测试通过；最终评审后修复，36 passed。
- **产出：** path guard → command guard → HITL → tool lookup/execute → event 的固定顺序。
- **commits：** `69ed768`, `b712616`。
- **人工干预：** 最终评审发现名为“approval approved”的测试实际使用 `echo ok`，没有命中 approval pattern。没有采用 reviewer 建议的真实 `pip install`，而是人工设计无副作用的 `approve-me` 标记，既覆盖审批路径又避免网络和环境依赖。
- **经验：** 测试名不能证明覆盖；必须沿控制流检查输入是否真正进入目标分支。

## M4：Feedback Loop（Tasks 14–17，主要贡献）

### 22:57 — Task 14：Validator

- **TDD：** 4 个新测试，全量 40 passed。
- **产出：** Import、pytest、ruff、mypy 四类 validator 及结构化 Finding。
- **commit：** `bb5bf70`。
- **人工/评审：** 明确本机只验证解析机制，真实命令链以 Linux 容器为运行真相源。
- **经验：** 把“工具退出码和文本”转成稳定数据模型，才能成为可回灌的反馈信号。

### 23:02 — Task 15：Failure Classifier

- **TDD：** 4 个新测试，全量 44 passed。
- **产出：** 按优先级短路的确定性失败分类。
- **commit：** `3276dbd`。
- **人工/评审：** 发现 brief 文本提及 SyntaxError，但实际代码没有单独分支；记录为规格精度问题，没有让 subagent自行扩展范围。
- **经验：** 当 prose 与给定接口不完全一致时，应显式记录而不是偷偷“修好”规格。

### 23:14 — Task 16：ValidatorPipeline

- **TDD：** 2 个新测试，全量 46 passed。
- **产出：** validator 有序执行、导入失败短路、结果分类。
- **commit：** `1dcc537`。
- **人工干预：** 原断言假设 Windows 宿主能直接解析容器内命令；按既定运行边界改为同时接受宿主导入失败与容器 pytest 失败路径。
- **经验：** 测试应验证机制契约，不应把偶然的宿主 PATH 当成产品语义。

### 23:20–23:30 — Task 17：CorrectionLoop

- **TDD：** 初版 47 passed；最终评审指出停机分支覆盖过薄，补测后 50 passed。
- **产出：** EDIT_APPLIED、VALIDATING、FEEDBACK_PREPARED、RETRY、DONE/BUDGET_HIT 等状态，以及 Pass、预算、重复失败、无动作四类停机条件。
- **commits：** `2db7fc3`, `fa33db3`。
- **人工干预：** 接受评审意见，增加 budget、stuck-cycle、None 三类分支测试；保持 `run_pipeline` 为可 monkeypatch 的模块级 seam。
- **经验：** 对主要贡献而言，只测 happy path 等于没有证明状态机；停机条件必须逐一形成确定性证据。

## M5：Memory 与 Orchestration（Tasks 18–20）

### 23:41 — Task 18：SQLite MemoryStore

- **TDD：** 1 个新测试，全量 51 passed。
- **产出：** 自实现 SQLite 写入与按 repo/kind 检索。
- **commit：** `6b7e7b5`。
- **人工/评审：** task brief 的类型注解引用 `MemoryRecord`，但只在函数内部导入，类定义阶段会失败；允许 subagent 增加一个顶层导入，并在报告中记录偏离。
- **经验：** “忠实执行计划”不能凌驾于可运行性；必要偏离应最小化并留下解释。

### 23:45 — Task 19：worktree 创建

- **TDD：** RED 为 worktree 模块不存在；GREEN 为 52 passed。
- **产出：** 基于 git subprocess 的隔离工作树创建。
- **commit：** `1d8d57d`。
- **人工/评审：** 使用临时 git 仓库验证，不依赖真实项目分支状态。
- **经验：** 隔离机制本身也要在隔离的 fixture 中测试，避免测试污染开发仓库。

### 23:49 — Task 20：AgentLoop

- **TDD：** 1 个新测试，全量 53 passed。
- **产出：** 组装系统上下文、按需记忆、CorrectionLoop、Run 状态与 RunFinished 事件。
- **commit：** `f6afc70`。
- **人工/评审：** 使用 `MockLLM([None])` 验证无动作停机和事件完成，不触发真实工具。
- **经验：** 外层编排测试应关注依赖连接和生命周期，而不是重复测试内层状态机细节。

## M6：CLI 与机制演示（Tasks 21–22）

### 2026-08-10 00:06–00:13 — Task 21：CLI

- **TDD：** 3 个新测试，全量 56 passed。
- **产出：** `run`、`test`、`credential` 命令和终端 renderer。
- **commits：** `aeef3fb`, `03c9377`；后续递归测试修复 `5623b4b`。
- **人工/评审：** 固定 `click==8.1.7` 解决 Typer 兼容问题。CI 后续暴露 `test` 子命令递归启动完整 pytest（连带 Docker build），人工定位后将单测改为 mock subprocess seam。
- **经验：** 命令派发单测应验证“调用了什么”和“如何传递退出码”，不能真的递归启动被测测试套件。

### 00:19 — Task 22：机制演示

- **TDD：** RED 为 demo 模块不存在；GREEN 为 57 passed。
- **产出：** 护栏拦截、失败反馈改变下一动作、重复失败停机三场景。
- **commit：** `7ed661b`。
- **人工/评审：** 使用 MockLLM 和 FrozenClock 保持无网络、可重复。
- **经验：** 演示不是另一套实现；最好复用生产内核，以少量脚本把关键行为串起来。

## M7：Distribution 与 CI（Tasks 23–25）

### 00:34–01:07 — Task 23：Docker

- **TDD：** 主机 57 passed + 1 skipped；Docker 测试在 CI 环境实际执行。
- **产出：** Python 3.12 slim、非 root 用户、CLI entrypoint、`.dockerignore`。
- **commits：** `c937f3d`, `e28f2d9`, `77e2644`。
- **人工干预：** 首轮镜像缺少 `PYTHONPATH` 和 `pyproject.toml`，修复后又发现 `/app` 由 root 拥有，非 root 用户无法写事件、缓存和 fixture；增加 chown 后镜像内测试恢复。
- **经验：** “镜像能 build”不等于“产品能以最终用户身份运行”；必须在镜像内执行真实入口和测试。

### 00:43–01:42 — Task 24：CI、GHCR 与 Release

- **TDD：** 初版 CI 结构测试从缺少文件的 RED 到 58 passed + 1 skipped；最终补强后 63 passed + 1 skipped。
- **产出：** `unit-test`、main 分支 `build-image`、GHCR 推送、带 digest 的 Release。
- **commits：** `d270ca3`, `4d10d11`, `615aee4`。
- **人工干预：** 评审指出测试只检查 job 名称，未防止 gate、权限和发布步骤被删，补充结构断言。镜像内不包含 `.github/`，因此将 repo-context CI 测试设为文件缺失时跳过。
- **经验：** CI 配置也应被测试，但测试必须区分“源码仓库上下文”和“产品镜像上下文”。

### 00:52–01:48 — Task 25：README、日志骨架与密钥扫描

- **TDD：** 当时全量 59 passed + 1 skipped。
- **产出：** README 必备章节、AGENT_LOG 骨架、pre-commit 与仓库密钥形状扫描。
- **commits：** `86ba033`, `7e5e112`, `7d200d9`。
- **人工干预：** 冷运行发现 src-layout 下裸 `python -m coding_harness` 无法导入，补充 `PYTHONPATH=src`；随后回填 M7 merge SHA 和镜像内验证结果。
- **经验：** README 命令必须在新 checkout 中实际执行，不能从开发者已激活的环境推断可用。

## 2026-08-10 — CI 故障闭环

### 11:38–11:55 — 三轮 CI 修复

- **技能与上下文：** 按失败日志逐层定位，不根据本地通过推断 CI 通过。
- **问题 1：** CLI 测试递归启动 pytest，最终递归执行 Docker build 并被 CI 以 exit 143 杀死；commit `5623b4b`。
- **问题 2：** 非 root 容器用户无法写 `/app`；commit `77e2644`。
- **问题 3：** 产品镜像未复制 `.github/`，repo-context 的 `test_ci` 在镜像内失败；commit `615aee4`。
- **最终结果：** GitHub Actions 的 `unit-test` 与 `build-image` 均成功，镜像与 Release 生成。
- **经验：** 本地测试、容器内测试和 CI host 测试是三个不同环境；只有逐层验证才能避免用一个环境的绿色替另一个环境背书。

## 2026-08-14 — 最终文档整理

### 17:42 — 源码可读性补充

- **工作：** 为 25 个源码模块增加中文模块说明、关键类/函数 docstring 和少量非平凡逻辑注释。
- **commit：** `e19c3ce`。
- **验证：** 当时远端 CI 63 passed / 1 skipped，CLI help 与三场景演示通过；GitHub Actions `unit-test`、`build-image` 成功并创建 Release。
- **人工判断：** 只补解释，不修改标识符、控制流和行为。
- **经验：** 文档化应解释边界和设计意图，而不是逐行翻译代码。

### 最终过程回顾

- **最有效的流程：** 陌生 agent 冷启动、逐 task TDD、两阶段评审和最终整分支复核。
- **最重要的人工判断：** 修正不可执行的 RED 顺序；拒绝有网络副作用的审批测试方案；补齐 CorrectionLoop 停机分支；依据 CI 日志区分递归测试、容器权限和 repo-context 三类故障。
- **主要偏离：** M2–M7 使用本地 fast-forward 连续集成，而非为每个 worktree 创建远端 PR；偏离过程和评审证据已保留在本日志与 task reports 中。
- **最终教训：** Superpowers 能持续提醒测试、评审和验证，但不能替代人对范围、测试真实性、环境边界和风险取舍的判断。
