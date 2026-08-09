# Cold Start Validation Report

## 1. 验证环境

* 使用的智能体类型与版本：OpenAI Codex（GPT-5 系列）；运行环境未暴露更细的模型构建号。
* 会话是否为全新会话：否。本轮是用户要求在同一 Codex task 中、规约修订后的续作。为降低续作上下文影响，本轮重新完整读取当前 SPEC 与 PLAN，并仍只把它们作为产品需求来源。
* 实际读取的需求文件：
  * `docs/superpowers/specs/2026-08-01-coding-agent-harness-design.md`（302 行）。
  * `docs/superpowers/plans/2026-08-09-coding-agent-harness.md`（2423 行）。
* 是否使用了额外上下文或 memory：未使用此前开发记录、memory 或口头产品背景，未读取其他项目文件内容。读取了 Superpowers 的计划执行、TDD、分支与验证流程说明，以及本地运行时位置；它们只约束执行方式，不作为产品需求。
* 隔离方式：从当前 `main` 新建独立分支 `codex/cold-start-task1-v2`。用户原有未跟踪内容 `.claude/` 与 `submission.jsonc` 未读取、未修改。
* 执行环境：Windows 宿主；无系统 Python 3.12、无 Docker。使用 Codex 随附的 Python 3.12.13 创建 `.venv`，安装 PLAN 锁定的直接依赖；pytest 8.2.2，GNU Make 4.4.1。
* 开始时间：2026-08-09 15:50 后（续作消息未单独记录秒级时间；本轮首次显式环境时间戳为 16:02:52 +08:00）。
* 结束时间：2026-08-09 16:11:54 +08:00。

## 2. 选择的任务

* Task 编号与名称：Task 1——项目脚手架、依赖、`make test`、gitignore。
* 选择原因：用户明确要求继续 Task 1；该 task 是 PLAN 的首个实现项，不消费其他 task 产出，并提供后续任务所需的包导入与测试入口。
* 前置依赖检查结果：无 task 依赖。修订后的 PLAN 已显式增加测试基础设施 bootstrap，解决原先 RED 命令依赖尚未创建 Makefile 的阻塞。
* 根据 PLAN 理解的完成标准：
  * 先创建不含产品行为的 `pyproject.toml`、`requirements.txt`、`Makefile`、`.gitignore`、`tests/__init__.py` 并安装依赖。
  * 再创建 `tests/test_scaffold.py`，运行 `make test`，必须因缺失 `coding_harness` 包而失败。
  * 仅创建 `src/coding_harness/__init__.py`，定义 `__version__ = "0.1.0"`。
  * 再运行 `make test`，必须得到 1 个测试通过。

## 3. 实施过程

按时间顺序：

1. 重新完整读取当前 SPEC（302 行）和 PLAN（2423 行）。确认实际修订位于 PLAN：新增权威文档路径、Task 1 bootstrap 和依赖安装说明；SPEC 内容未呈现对应 bootstrap 步骤。
2. 创建独立分支 `codex/cold-start-task1-v2`。
3. 按 Task 1 Step 1 创建测试基础设施：`pyproject.toml`、`requirements.txt`、`Makefile`、`.gitignore`、`tests/__init__.py`。此时没有创建 `src/coding_harness/`。
4. 系统 Python Launcher 没有 Python 3.12，Docker 命令也不存在。检查本地只读运行时目录后，找到 Codex 随附 Python 3.12.13，以它创建 `.venv`。
5. 首次 `pip install -r requirements.txt` 在 124 秒后超时，且 pytest 尚未安装；延长时限重试同一锁定依赖安装，最终成功。随后 `pip check` 输出 `No broken requirements found.`。
6. 编写失败测试 `tests/test_scaffold.py::test_package_importable`。它捕获的破坏是：公开包无法导入，或公开版本不等于字面量 `0.1.0`。
7. 第一次测试失败命令：在 `.venv` 的 `Scripts` 目录置于 PATH 后执行 `make test`。

   关键输出：

   ```text
   pytest -q
   F [100%]
   E ModuleNotFoundError: No module named 'coding_harness'
   FAILED tests/test_scaffold.py::test_package_importable
   1 failed in 0.09s
   ```

   失败原因与 PLAN 的 RED 预期一致，且不是 Makefile、pytest 或测试语法错误。
8. 编写最小实现 `src/coding_harness/__init__.py`，仅包含 `__version__ = "0.1.0"`。
9. 测试变绿命令：以相同 `.venv` PATH 执行 `make test`。

   关键输出：

   ```text
   pytest -q
   . [100%]
   1 passed in 0.02s
   ```

10. 是否进行了重构：否。实现已是满足单一行为的最小形式。
11. 最终修改的文件：
    * `.gitignore`
    * `Makefile`
    * `pyproject.toml`
    * `requirements.txt`
    * `src/coding_harness/__init__.py`
    * `tests/__init__.py`
    * `tests/test_scaffold.py`
    * `COLD_START_REPORT.md`

## 4. 暂停点与问题

未遇到需要因 SPEC/PLAN 歧义而暂停的问题。原先的阻塞已经由当前 PLAN 的以下设计唯一解决：

* Task 1 明确声明 bootstrap 文件不实现 `coding_harness` 行为，允许先于 RED 创建。
* RED 命令、预期异常、最小产品文件和 GREEN 结果均已明确。
* PLAN 明确给出宿主虚拟环境与容器两种依赖安装方式。

执行中出现两项环境问题，但均能按当前 PLAN 和现有环境确定性解决，没有要求规约补充：系统缺少 Python 3.12 与 Docker；首次依赖安装超时。符合版本的本地 Python 运行时可用，重试同一安装命令后成功。

## 5. 规约理解偏差

* 最初理解：用户称“修改了 SPEC”，因此预期 bootstrap 规则会出现在 SPEC。
* 实施后发现：SPEC 仍为 302 行且产品设计内容未体现 Task 1 bootstrap；实际解决阻塞的是 2423 行的 PLAN，其中新增了 19 行左右的 Task 1/权威路径修订。
* 缺陷类型：用户描述与实际修改文件不一致，但当前 PLAN 自身足以唯一实施 Task 1，不构成代码阻塞。
* 仍可能让不同智能体得到不同执行路径的位置：
  * 全局约束称 Windows 宿主必须在 Docker 内运行；Task 1 又显式给出 Windows 宿主虚拟环境安装方式。本次将更具体的 Task 1 指令理解为 scaffold 冷启动例外。
  * `requirements.txt` 只精确固定了九个直接依赖，传递依赖仍由 pip 当时解析。不同时间安装可能得到不同传递版本，尽管 Task 1 的单测不受影响。

## 6. 产出与预期差距

* PLAN 描述的预期产出：可导入的 `coding_harness` 0.1.0 包、锁定直接依赖、统一 `make test` 入口、gitignore 与一条经过 RED/GREEN 的 scaffold 测试。
* 实际完成的产出：与上述预期一致；另按冷启动要求生成本报告，并创建隔离分支。
* 未完成部分：无 Task 1 功能缺口。后续 Task 2–25 均未实施，符合本次只完成一个 task 的范围。
* 阻塞原因：无当前阻塞。
* 如果继续实施，必须先修改哪些规约：Task 2 不依赖必须修改的阻塞规约；下列建议属于非阻塞澄清。

## 7. 建议修订

* 问题：Windows/Docker 全局硬规则与 Task 1 宿主虚拟环境步骤表面冲突。
* 原文：全局约束“Windows 宿主须在 Docker 内运行”；Task 1 Step 1 同时给出“宿主冷启动（可选虚拟环境）”的 Windows 命令。
* 建议改为：明确“Windows 宿主不得直接运行 harness 的 worktree/agent 功能；Task 1 的纯 scaffold 单测可作为例外在 Python 3.12 宿主虚拟环境运行。Task 19 及真实 worktree 集成验证必须在 Docker Linux 内运行”。
* 修改理由：让不同智能体在没有 Docker 的 Windows 冷启动环境中作出相同决定，同时不削弱产品运行边界。
* 应修改文件：`PLAN.md`
* 严重程度：重要

* 问题：依赖“精确锁定”的范围不明确。
* 原文：全局约束“依赖在 requirements.txt 中精确锁定版本”；Task 1 只列出九个直接依赖的固定版本。
* 建议改为：明确该要求仅指直接依赖，或提交包含哈希/传递依赖版本的完整 lockfile，并规定 Docker、CI、本地统一从 lockfile 安装。
* 修改理由：当前 pip 会解析未固定的传递依赖，长期不能保证 cloud/local/CI 得到完全相同的环境。
* 应修改文件：`PLAN.md`
* 严重程度：重要

* 问题：规约修订说明与实际文件名称容易被口头描述混淆。
* 原文：本轮用户称 SPEC 已修改；实际 bootstrap 修订位于 PLAN。
* 建议改为：后续冷启动指令直接引用 PLAN 新增的两个权威相对路径，并在变更说明中明确修改的是 SPEC、PLAN 或两者。
* 修改理由：减少陌生智能体定位错误版本或误判修订未生效的风险。
* 应修改文件：`PLAN.md`
* 严重程度：一般

## 8. 最终结论

**修正部分非阻塞问题后可以继续。**

当前 SPEC + PLAN 已足以让陌生智能体严格按 TDD 完成 Task 1。Windows 执行边界和传递依赖锁定仍值得澄清，但不影响本 task 的接口、数据模型、代码或测试结果。
