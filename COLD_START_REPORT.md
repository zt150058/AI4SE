# Cold Start Validation Report

## 1. 验证环境

* 使用的智能体类型与版本：OpenAI Codex（GPT-5 系列）；当前运行环境未暴露更细的模型构建号，因此不臆测具体版本号。
* 会话是否为全新会话：是。本次按“陌生智能体”冷启动会话执行。
* 实际读取的需求文件：
  * `docs/superpowers/specs/2026-08-01-coding-agent-harness-design.md`（302 行，作为用户所指的 SPEC）。
  * `docs/superpowers/plans/2026-08-09-coding-agent-harness.md`（2404 行，作为用户所指的 PLAN）。
* 是否使用了额外上下文或 memory：未使用任何此前对话、memory、开发记录或口头背景；未读取其他项目文件内容。仅读取了当前执行环境要求的 Superpowers 流程技能（worktree、TDD、计划执行、完成前验证）并执行了只读 Git/环境检查。这些内容只约束执行方法，不作为产品需求来源。
* 隔离方式：独立分支 `codex/cold-start-validation`。创建分支前存在用户未跟踪内容 `.claude/` 与 `submission.jsonc`，本次未读取、未修改。
* 开始时间：2026-08-09 15:42:55 +08:00。
* 结束时间：2026-08-09 15:50:23 +08:00。

## 2. 选择的任务

* Task 编号与名称：Task 1——项目脚手架、依赖、`make test`、gitignore。
* 选择原因：Task 1 是 PLAN 中唯一明确不消费其他 task 产出的实现任务，也是其余 Python 模块获得包导入路径与统一测试入口的基础。
* 前置依赖检查结果：无 task 前置依赖。当前仓库没有 `Makefile`，也没有 `tests/test_scaffold.py`；GNU Make 4.4.1 可用。
* 根据 PLAN 理解的完成标准：
  * 创建 `pyproject.toml`、`requirements.txt`、`Makefile`、`.gitignore`、`src/coding_harness/__init__.py`、`tests/__init__.py` 与 `tests/test_scaffold.py`。
  * `coding_harness.__version__` 等于 `0.1.0`。
  * 严格观察 RED：`make test` 因 `ModuleNotFoundError: coding_harness` 失败。
  * 完成最小实现后，`make test` 显示 1 个测试通过。

## 3. 实施过程

按时间顺序：

1. 完整读取 SPEC 与 PLAN，并逐项检查 PLAN 中 25 个 task 的依赖。
2. 选择无 task 前置依赖的 Task 1。
3. 在写入测试前检查 Task 1 的 TDD 步骤，发现 RED 命令与测试运行器创建顺序互相矛盾。
4. 按冷启动规则立即暂停；未编写失败测试，也未编写任何生产实现，以免通过猜测改变 PLAN 规定的执行顺序。
5. 第一次测试失败的命令和关键输出：未运行。原因是当前不存在 `Makefile`，执行 PLAN 指定的 `make test` 只会验证测试入口缺失，而不会运行新测试并产生 PLAN 指定的 `ModuleNotFoundError: coding_harness`。
6. 测试变绿的命令和关键输出：未运行；任务在 RED 阶段前被阻塞。
7. 是否进行了重构：否。
8. 最终修改的文件：仅新增 `COLD_START_REPORT.md`；未修改任何产品代码、测试、SPEC 或 PLAN。

## 4. 暂停点与问题

### 暂停点 1：Task 1，Step 1 与 Step 2 之间

* 暂停位置：准备写 `tests/test_scaffold.py` 并执行首次 RED 验证时。
* 对应的 SPEC/PLAN 原文：

  > Task 1 Step 2：`Run: make test`；`Expected: FAIL — ModuleNotFoundError: coding_harness`

  > Task 1 Step 3：创建 `Makefile`，其 `test` target 执行 `pytest -q`。

  > 全局约束：用 `make test`（即 `pytest -q`）运行测试。

* 暴露出的规约缺陷：PLAN 要求在 Makefile 存在之前通过 Makefile 运行测试。规定的失败命令在规定时点不可执行到 pytest，因此无法产生规定的失败原因，也无法证明失败测试真正捕获了缺失的包行为。
* 为什么现有描述不足以支持唯一实现：文档没有说明测试基础设施是否可作为 TDD 前置 bootstrap 创建，也没有授权使用替代 RED 命令。
* 可能的不同解释：
  1. 先创建 `Makefile`（可能还包括 `pyproject.toml`）作为测试基础设施，再写/运行失败测试。
  2. 保持文件创建顺序，但首次 RED 改用 `python -m pytest -q tests/test_scaffold.py`。
  3. 直接运行 `make test`，把“没有 Makefile/target”接受为失败证据。
* 不同解释的影响：
  * 解释 1 会改变 PLAN 明示的 Step 3 文件创建时点，并需要界定哪些 scaffold 文件不算 production implementation。
  * 解释 2 会改变 PLAN 指定的验证命令，并依赖环境中 pytest 已预装或先安装依赖。
  * 解释 3 无法执行测试文件，违反严格 TDD 中“失败必须由缺失行为而非测试基础设施错误导致”的要求，也与 PLAN 指定的预期错误不一致。
* 拒绝擅自采用的假设：不假设可以提前创建 Makefile；不假设可以用 pytest 命令替代 `make test`；不把“Makefile 不存在”当作测试行为的有效 RED 证据。
* 需要补充进 SPEC/PLAN 的问题：
  1. Task 1 的 RED 阶段应使用哪条可在 Makefile 尚不存在时执行的精确命令？
  2. 是否允许在失败测试之前创建纯测试基础设施文件；若允许，具体包括哪些文件？
  3. 若采用直接 pytest 命令，依赖安装应发生在何时、使用什么精确命令？

## 5. 规约理解偏差

* 最初理解：Task 1 是一个标准的 RED-GREEN scaffold task——先新增导入测试，通过统一入口观察 `ModuleNotFoundError`，再创建包与工程文件使测试通过。
* 实施前发现的冲突：统一入口 `make test` 本身也是 Task 1 的待创建产物，导致它在 RED 阶段不可用。
* 缺陷类型：任务拆分与步骤排序问题，同时存在测试 bootstrap 边界定义缺失。
* 容易导致不同智能体产生不同实现的位置：有的智能体会提前创建 Makefile，有的会私自改用 pytest，有的会把 make 的基础设施错误当作有效 RED；三者留下的 TDD 证据和提交内容均不同。

除此之外，Task 1 的目标包名、版本号、文件路径、依赖版本、gitignore 条目和最终 GREEN 命令均可仅凭 PLAN 唯一确定。

## 6. 产出与预期差距

* PLAN 描述的预期产出：完整 Task 1 scaffold、一个先红后绿的导入测试，以及通过的 `make test`。
* 实际完成的产出：完成 Task 选择、依赖审查、TDD 可执行性审查与本冷启动报告；建立独立分支。
* 未完成部分：Task 1 的测试与所有实现文件均未创建；未产生 RED/GREEN 测试输出；未提交 task 实现。
* 阻塞原因：PLAN 的 RED 验证命令依赖于 GREEN 阶段才创建的 Makefile。
* 如果继续实施，必须先修改的规约：至少修改 PLAN Task 1 的 bootstrap/RED 步骤顺序及精确命令；SPEC 的产品设计无需因此改动。

## 7. 建议修订

* 问题：Task 1 的 RED 命令依赖尚未创建的 Makefile。
* 原文：`Step 2: Run: make test`；`Step 3` 才创建 `Makefile`。
* 建议改为：在 Task 1 增加显式的“Step 0：测试基础设施 bootstrap”，只创建 `Makefile`、pytest 所需的最小 `pyproject.toml` 并安装锁定依赖；明确这些文件不实现 `coding_harness` 行为。随后创建 `tests/test_scaffold.py`，运行 `make test`，预期 `ModuleNotFoundError: coding_harness`；GREEN 阶段再创建 `src/coding_harness/__init__.py` 及其余非测试 scaffold 文件。
* 修改理由：使 PLAN 指定的 RED 命令实际运行测试，并确保失败原因是缺失产品行为而不是缺失测试入口。
* 应修改文件：`PLAN.md`
* 严重程度：阻塞

* 问题：依赖安装时点没有写入 Task 1 步骤。
* 原文：全局约束列出精确依赖版本；Task 1 创建 `requirements.txt`，但没有安装命令。
* 建议改为：在 Task 1 明确虚拟环境/容器中的依赖安装命令、执行时点，以及 RED 阶段 pytest 的可用前提；同时说明 Windows 冷启动验证是否允许在宿主执行 scaffold 测试，或必须提供 Docker bootstrap 命令。
* 修改理由：不同新环境可能没有 pytest，且 SPEC/PLAN 将容器 Linux 定义为唯一运行真相源；缺少精确环境步骤会让首次失败原因不一致。
* 应修改文件：`PLAN.md`
* 严重程度：重要

* 问题：用户称需求文件为 `docs/SPEC.md`、`docs/PLAN.md`，仓库实际采用日期化嵌套路径。
* 原文：实际文件为 `docs/superpowers/specs/2026-08-01-coding-agent-harness-design.md` 与 `docs/superpowers/plans/2026-08-09-coding-agent-harness.md`。
* 建议改为：在冷启动入口说明中写出两份文档的精确仓库相对路径，或提供稳定的 `docs/SPEC.md`、`docs/PLAN.md` 链接/副本并声明其权威性。
* 修改理由：避免陌生智能体在多个日期化版本并存时选择错误规约；本次只有各一个候选文件，尚可唯一映射。
* 应修改文件：`PLAN.md`
* 严重程度：一般

## 8. 最终结论

**存在阻塞性歧义，暂不应开始正式实现。**

阻塞范围当前集中在第一个实现任务的 TDD bootstrap 顺序。修订 PLAN 使首次 RED 命令能在不提前实现产品行为的前提下真实运行测试后，陌生智能体才可继续 Task 1。
