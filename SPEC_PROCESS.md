# SPEC_PROCESS.md — 与 Superpowers 协作生成 Spec 与 Plan 的过程

> AI4SE 期末项目 · A · Coding Agent Harness
> 本文件记录与 `brainstorming` + `writing-plans` 技能协作生成 `SPEC` 与 `PLAN` 的全过程，
> 含关键节点、至少三轮关键迭代的对话节选与处理决策、AI 提议与我的取舍，以及对 brainstorming 技能的反思。
> 对应通用要求 §4.3 / §4.5。

---

## 一、协作概览

- **使用的技能**：`superpowers:brainstorming`（设计探索）→ `superpowers:writing-plans`（实现计划）。
- **产出**：`docs/superpowers/specs/2026-08-01-coding-agent-harness-design.md`（SPEC）+ `docs/superpowers/plans/2026-08-09-coding-agent-harness.md`（PLAN）。
- **核心命题**：Agent = LLM + Harness。本项目用 Superpowers 这个 harness 去造另一个 harness（Coding Agent Harness），从而对方法论形成第一手批判性理解。
- **流程纪律**：在 SPEC + PLAN 完成并通过冷启动验证之前，不写任何实现代码（通用要求 §4）。

---

## 二、brainstorming 关键节点（智能体追问了哪些好问题）

brainstorming 技能采用"一次一个问题、优先多选、带推荐项"的对话节奏，把一个模糊命题逐步收敛为可签字确认的设计。它追问的关键问题与我的回应：

| # | 智能体追问 | 我的选择 | 该问题为何重要 |
|---|---|---|---|
| Q1 | 哪个维度做深（主要贡献）？ | **反馈闭环** | 决定整个设计重心；§A.4-D 要求六维有最低实现、其中一维做深 |
| Q2 | 一次运行解决什么形态的 coding 任务？ | **修复型闭环** | 决定反馈信号是什么、闭环怎么设计 |
| Q3 | 用什么语言？ | **Python** | 决定 TDD 体验、mock-LLM 简洁度、分发形态 |
| Q4 | 真实 LLM 接哪个供应商？ | **Anthropic Claude** | 决定凭据威胁模型与抽象层签名 |
| Q5 | WebUI 的角色是什么？ | （初版）观察+审批 →（终版）CLI-only | 同时决定 HITL 交互模型，影响最大 |
| Q6 | 收集哪些客观反馈信号、失败分类成什么？ | 测试+导入/lint+类型检查 | 这是深度维度本身，必须能解析→判定→回灌 |
| Q7 | agent 工具在什么环境执行？ | worktree + 路径围栏 | 同时决定 scope-fence 护栏与分发形态 |

**最让我修正原设想的两个追问**：

1. **Q5（WebUI 角色）引发的范围张力**：智能体在读到通用要求 §五.9"必须提供可访问的 WebUI 接口"后，主动指出这与 Coding Agent Harness 天然的 CLI/无头形态存在张力——这不是我事先想清楚的的地方。它没有替我决定，而是把张力摆出来，迫使我面对"WebUI 到底是内核的一部分，还是一层薄薄的观察/审批壳"。最终我把 WebUI 定位为"消费 EventLog + 审批"的薄壳，而非内核组件——这一边界划分直接决定了内核能否在无浏览器下离线单测。

2. **Q6（反馈信号）让我意识到"lint/类型噪声"陷阱**：我原本想"信号越多越好"，智能体提示 ruff/mypy 噪声会模糊修复方向。最终我采纳了"测试为主信号、lint/类型为约束（仅 `E/F` 阻塞、忽略样式 `D/W`）+ 每轮只展示最高优先级失败"的双闸设计。

---

## 三、至少三轮关键迭代（对话节选与处理决策）

### 迭代 1：架构方案——从"单循环"到"双层状态机 + 事件日志"

**背景**：智能体在问清 Q1–Q7 后，提出三种架构方案：

> **方案 1（单 ReAct 循环）**：反馈校验器只是 agent 调用的"另一个工具"，分类塞进结果文本。*Pro：最简。Con：反馈闭环无一等结构，不可独立单测，与深度要求冲突。*
> **方案 2（双层：任务循环 + 修正循环）**：外层任务循环 + 内层修正循环状态机（编辑→校验→分类→注入反馈→重试）。修正循环是独立的、可用 mock LLM 单测的状态机。
> **方案 3（事件溯源 reducer）**：每步为不可变事件，循环是 reducer。

**我的决策**：选**方案 2**，并借用方案 3 的"轻量事件日志"喂给 WebUI/HITL。

> **修订前（我的初版设想）**：一个 ReAct 主循环搞定一切，反馈就当作工具调用。
> **修订后**：双层状态机 + append-only EventLog。

**理由**：方案 2 让"反馈闭环"这个重点维度成为**一等、可隔离、可单测的状态机**——正好命中 §A.4(C) 的硬判据（移除真实 LLM 后仍能确定性单测）。事件日志让 WebUI 观测与 HITL 暂停/恢复天然有 checkpoint，又不背方案 3 的全 reducer 抽象债。这是本次设计最关键的一次收敛。

---

### 迭代 2：分发方案——三次摇摆（Docker+云 → Docker-only → CLI-only+Release）

这是贯穿全过程的最高频迭代，源于 §五.9"公网 WebUI URL"与项目天然 CLI 形态的根本张力。

**第 1 版（初稿）**：Docker + Fly.io 云部署，提供公网 WebUI URL。
- 智能体当时提示：Coding Agent Harness 本是无头/CLI 系统，但 §五.9 要求公网 WebUI。我把 WebUI 当作必须的薄壳，云托管跑同一镜像提供 URL。

**第 2 版（我第一次推翻）**：我要求"只做 Docker，删云部署、删 PyPI"。
- 智能体没有沉默照办，而是**主动标红冲突**：

> "⚠️ 通用要求 §五.9 写明'必须提供应用可访问的 WebUI 接口'……你的修订意味着没有 always-on 公网 URL……这是真实的、可计分的冲突。"

> 它给了两个调和选项：①诚实 scoping（保留 Docker-only，文档说明不满足 §五.9 并接受风险）；②一次性临时隧道（cloudflared/ngrok）按需产出 URL，不引入托管平台。

**第 3 版（我据此改主意）**：看到冲突被摆明后，我选择"Docker + 云部署，不要 PyPI"——即第 1 版的精简。智能体据此写了 §7.2 终版（GHCR 镜像 + Fly 拉取同一镜像 + `fly secrets` 注入 key + `https://<app>.fly.dev` 作为 §五.9 交付）。

**第 4 版（最终，CLI-only + Release）**：我再次要求彻底删云，改为"CLI-only + Docker + GitHub Release"，`is_deployed: false`，以固定版本 GitHub Release 链接（`deploy_release_url`）为交付。
- 智能体据此删除整个 WebUI/API 模块（FastAPI/SSE/HTTP 审批/端口暴露）、删除 Fly/Render/公网 URL，改 `ApprovalGateway` 生产实现为 `ConsoleApprovalGateway`（交互式 TTY 批准/拒绝、非交互默认拒绝、测试用 `ScriptedApprovalGateway`），Docker 入口改为 `python -m coding_harness`，删 `EXPOSE`/`HEALTHCHECK`。

> **修订前 → 修订后（关键 diff）**：
> - 分发：`Docker + Fly.io + 公网 URL` → `Docker + GHCR + GitHub Release 链接（is_deployed: false）`
> - 观察/审批：`FastAPI WebUI + SSE` → `终端结构化输出 + JSONL EventLog`
> - 审批生产实现：`WebUI POST approve` → `ConsoleApprovalGateway`（TTY approve/deny，非交互 deny）
> - 用户故事 2/3/5：`访问 WebUI/在 WebUI 审批` → `CLI 运行/CLI 实时查看/交互式 CLI 审批`
> - 架构图：删除 WebUI/API 节点，加入 CLI 与 `ConsoleApprovalGateway`
> - Dockerfile：`serve` 入口 + `EXPOSE 8000` + `HEALTHCHECK` → `python -m coding_harness`，无端口

**为什么摇摆了三次**：这正反映 §五.9 的要求与"深度优先、不加无关复杂度"的项目哲学之间的真实拉扯。最终 CLI-only + Release 是把"可复现运行环境"（Docker）与"获取入口"（Release 链接）干净分离——Docker 只负责提供可复现环境，不扩展成部署平台或包管理。

---

### 迭代 3：用户故事编号事故——AI 出错，我质询修正

**事故**：在把 WebUI 相关用户故事改写为 CLI 等价物时，智能体一次编辑误把"故事 4（agent 获得反馈自我修正）"覆盖成了"CLI 审批"故事，导致出现两个"故事 4"且丢失了 agent 反馈故事。

> **修订前（错误态）**：
> 4. 作为开发者，我想在交互式 CLI 中对危险动作批准或拒绝……（误植）
> 4. 作为 agent 自身，我想获得反馈自我修正……（编号重复）
> 5. 作为开发者，危险动作护栏+审批……

**我的处理**：我注意到编号错乱，要求智能体修正。它删除误植的"故事 4"，把 CLI 审批细节并入"故事 5（危险动作护栏 + 交互式 CLI 审批 + 非交互默认拒绝 + 超时）"，恢复 agent 反馈故事为故事 4。

> **修订后（正确态）**：
> 4. 作为 agent 自身，获得结构化反馈与失败分类，据此改变下一步……
> 5. 作为开发者，危险动作护栏 + 交互式 CLI 审批（非交互默认拒绝、超时自动拒绝）……

**教训**：这暴露了 AI 协作中"看似机械的编辑也会引入语义错误"——所以我坚持在每次大改后做一次全文 grep 复核（这次最终用 `grep WebUI|FastAPI|SSE|Fly|8000` 确认旧方案关键词仅残留在"删除/否定"语境，无主动使用残留）。**人控的价值就体现在这种"机械操作后的语义校验"上**。

---

## 四、哪些建议是 AI 提出、我采纳/推翻

**采纳（AI 提议）**：
- 反馈闭环作为重点维度（AI 推荐）→ 采纳。
- Python 作为语言（AI 推荐）→ 采纳。
- Anthropic Claude 作为供应商 → 采纳。
- worktree + 路径围栏作为执行环境 → 采纳（护栏可作纯函数单测）。
- 方案 2 双层状态机 + 轻量事件日志 → 采纳。
- "测试为主信号、lint/类型为约束 + 每轮只展示最高优先级失败" → 采纳。
- 25 个 TDD 任务 + 每任务"写失败测试→运行失败→最小实现→通过→提交"五步 → 采纳。

**推翻/修正（我的决定）**：
- AI 初版推荐"Docker + Fly.io 云部署"以满足 §五.9；我最终推翻为"CLI-only + GitHub Release，`is_deployed: false`"。AI 据此调整而非坚持原议。
- AI 把 WebUI 当薄壳保留；我决定彻底删 WebUI，改纯 CLI + `ConsoleApprovalGateway`。
- 用户故事编号事故中，我推翻 AI 的错误编辑，强制重排。

**AI 的克制与价值**：在我要求"删云、删 WebUI"时，AI 没有沉默照办，而是先标红 §五.9 的硬冲突——这种"不服从但诚实"的行为，比"你说删我就删"更有价值，因为它守住了"做对了吗"这一工程师判断。

---

## 五、冷启动试运行（§4.5，陌生智能体验证）——已执行

**执行情况**：用 OpenAI Codex（GPT-5 系列）做陌生智能体冷启动，全新 session，未导入本会话历史或 memory，仅凭 SPEC + PLAN 自主推进。报告见 `COLD_START_REPORT.md`。隔离分支 `codex/cold-start-validation`。它选择 Task 1（项目脚手架），在 RED 阶段前**主动暂停**，未编写任何产品代码或测试——严格符合 §4.5"遇不确定即暂停询问，而非凭猜测继续"。

**Codex 暴露的 spec 缺陷（修订前后 diff）**：

1. **Task 1 RED bootstrap 顺序（阻塞，真实 bug）**：
   - 修订前：Step 2 `Run: make test`，`Expected: ModuleNotFoundError`；但 `make test` 依赖 Step 3 才创建的 `Makefile`/`pyproject.toml`，且依赖未安装——RED 命令在规定时点不可执行。
   - 修订后：拆为"Step 1 测试基础设施 bootstrap（`Makefile`/`pyproject.toml`/`requirements.txt`/`.gitignore`/`tests/__init__.py` + 安装依赖，不含产品行为）→ Step 2 写失败测试 → Step 3 RED → Step 4 GREEN"。明确：bootstrap 文件不实现 `coding_harness` 行为，TDD 允许先于 RED 创建。
   - 处理决策：采纳 Codex 的"Step 0 bootstrap"建议。我自审时漏看此缺陷——这印证 §4.5"你与主 agent 沉淀的隐性上下文会让你高估 spec 清晰度"。

2. **依赖安装时点缺失（重要，真实 gap）**：
   - 修订前：`requirements.txt` 列了锁定版本，但全程无 `pip install` 命令与时点。
   - 修订后：Task 1 Step 1 显式写入 `pip install -r requirements.txt`（含宿主 venv 与容器两条路径）。
   - 处理决策：采纳。

3. **文档路径命名（一般）**：用户向 Codex 指向"docs/SPEC.md/docs/PLAN.md"，实际为日期化嵌套路径。Codex 因候选唯一仍能映射，未误读。
   - 修订后：在 PLAN 全局约束加"权威文档路径"一行，写明两份文档精确相对路径，并要求冷启动时显式指向。
   - 处理决策：采纳为低优先级护栏。

**Codex 未触及的更深缺陷（我自审预判，仍未验证）**：因 Task 1 阻塞，worktree 根路径约定、`Event` payload schema 字段、`MockLLM` `None` 语义、`run_pipeline` monkeypatch 注入点均未被测试。这些保留为实现期重点复核项，不假装已验证。

**对 SPEC/PLAN 的总修订**：仅改 PLAN（Task 1 重构 + 全局约束加权威路径）；SPEC 产品设计无需改动（Codex 亦确认"SPEC 的产品设计无需因此改动"）。修订已提交。

**结论**：冷启动达成了它的设计目的——在最廉价的时点（写第一行代码前）逼出一个我自审漏掉的真实 TDD 顺序 bug。这正是"陌生智能体在你未明文写下的每个假设处受阻"的实证。

---

## 六、反思：brainstorming 技能在本项目里的得失

**做得好的地方**：
- **一次一问 + 多选带推荐**：把"模糊命题 → 可签字设计"的认知负担拆到最小，我几乎每个问题都能在 3–4 个选项里快速决策。
- **主动标红范围张力**：WebUI vs §五.9 的冲突是它先指出的，这正是单人项目中最接近"同侪评审"的反馈——它没有替我回答"做什么"，但守住了"别漏看硬要求"。
- **方案对比步骤**：要求给出 2–3 个真实不同的架构方案及取舍，而非直接给一个答案。方案 2 的"反馈闭环作为可隔离单测的一等状态机"正是被这一步逼出来的。
- **HARD-GATE**：强制在 SPEC 签字 + PLAN 完成前不写代码，杜绝了"边想边写"的漂移。

**让我不满的地方**：
- **过程偏长、偏程式化**：8 个澄清问题后才进入设计，部分问题（如语言/供应商）其实是低风险决策，AI 完全可以替我默认后由我在设计评审时推翻，以减少往返。
- **可视化伴侣未触发**：架构图与状态机图本可受益于可视化对比，但技能要求"just-in-time 且仅当问题真正更适合展示时"才提议；AI 判断 ASCII 已足够，故全程未提议。结果状态机图只能用 ASCII，评审时不如真正的图直观——这是"克制"与"有用"之间的一次取舍，我倾向认为此处应更主动。
- **PLAN 的 TDD 全代码步骤极长/极耗 token**：writing-plans 要求每步含实际代码、禁占位符，这保证质量但使 PLAN 文档巨大（~2400 行）。对"每个 subagent 一次会话内完成一个 task"而言，粒度合理，但作为人类通读评审则偏重。
- **编号事故暴露的脆弱性**：技能依赖 AI 的精确编辑，而 AI 在机械改写用户故事时仍会引入语义错误。这印证了"过程脚手架能守纪律，但不能替我守语义正确性"——评审仍是不可外包的人工责任。

**对 Superpowers 方法论的批判**：它假设 (a) spec 写得够清楚，陌生 agent 就能照做；(b) TDD 强制能放大而非阻碍 AI 协作；(c) subagent 颗粒度可由 plan 固定。在本项目里：(a) 大致成立但隐性假设（worktree 约定、事件 schema、mock DSL 语义）仍多，需冷启动验证；(b) 待实现期检验；(c) "每 task 2–5 分钟"与"双层状态机 + WebUI/CLI + 分发"这种规模有张力——深度维度（CorrectionLoop）一个 task 装不下，需在 PLAN 中显式标注重点维度的 task 可适度放大。这些假设的边界，正是本反思要交给评审者的"第一手回答"。

---

*本文件为过程证据，与 SPEC/PLAN 同步演进；冷启动试运行完成后将回填 §五实际结果。*
