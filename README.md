# YZJ 团队共享技能库（skills）

## common 通用加载目录（2026-10-28）

本仓库以 `common/` 为**模型无关的唯一内容源**：原 `.claude/skills/`（Claude Code 专属路径）迁移为 `common/skills/`，技能正文完成宿主无关化——宿主差异一律写成行内映射「（Claude Code：X；其他宿主：Y）」。曾经的 Codex 生成式适配层（`.agents/` + 同步/校验脚本）已删除：**任何模型接入都不再需要定制化处理**，拷贝 / 引用 common 内容 + 一个入口文件即可。

```text
skills/
├── AGENTS.md                  # 通用宿主常驻入口（任何模型从这里开始）
├── CLAUDE.md                  # Claude Code 维护会话入口（@AGENTS.md + 专属路由）
├── common/skills/<name>/      # 通用流程技能（源基线；装到目标项目根目录层）
├── backend/<name>/            # 后端规范技能（YZJ 四层 + MyBatis-Flex 同栈）
├── frontend/<name>/           # 前端规范技能（Vue 3 + Naive UI 同栈）
├── templates/
│   ├── CLAUDE.md.template     # Claude Code 项目入口模板
│   ├── AGENTS.md.template     # 其他宿主项目入口模板（含不可删减的「执行门禁」）
│   ├── common/rules/          # 常驻规则模板（协作原则 / 契约速查，宿主无关）
│   └── .document/             # 项目文档骨架
└── scripts/
    └── verify-baseline.sh     # 基线校验（兼容 .claude/skills 与 common/skills 两种目标布局）
```

### 接入方式（按宿主）

| 宿主 | 安装目标 | 入口 |
|------|---------|------|
| **Claude Code** | `common/skills/*` → 项目根 `.claude/skills/`；`templates/common/rules/*` → `.claude/rules/`；`backend/`、`frontend/` → 各子仓 `.claude/skills/`（宿主只认 `.claude/`，属硬约束） | `templates/CLAUDE.md.template` 实例化 CLAUDE.md |
| **其他模型** | `common/skills/*` → 项目根 `common/skills/`，`templates/common/rules/*` → `common/rules/`（内容同源直用，无需任何适配） | `templates/AGENTS.md.template` 实例化 AGENTS.md（显式引用技能与规则） |
| **多宿主** | 以 `common/` 为内容源，另复制一份到各级 `.claude/`；两份同源、re-sync 时一起更新 | 两个入口并存，CLAUDE.md 首行 `@AGENTS.md` |

**两条硬约定**贯穿所有入口与模板（详见 `common/skills/project-onboarding`）：

1. **相对路径**：入口文件中的加载引用一律相对入口文件所在目录，**禁止绝对路径**——同一父目录常并存多个项目，且项目会迁移 / 改名；验收口径是"项目整体移动后引用仍成立"。
2. **执行门禁不得删减**：AGENTS.md 模板的「执行门禁」节是防接入宿主偷懒的兜底（必读全文 / 不跳审查 / 自证产出 / 不虚报验证 / 批准须显式）。

### 在本仓库使用

从 **`skills/` 仓库目录**启动会话：Claude Code 自动加载根 CLAUDE.md（`@AGENTS.md`），其他宿主读 AGENTS.md。本仓库的技能源在 `common/skills/`，**任何宿主都不自动发现**——按入口文件的路由表读取对应 SKILL.md 全文执行。工作目录若是外层 `framework/`，直接指定相应 SKILL.md 读取。

### 维护与同步

- **单一源、无同步脚本**：修改规范直接改 `common/skills/`、`backend/`、`frontend/` 下的源文件；宿主差异用行内映射表述，不生成宿主专属副本。
- 技能 `name` 与目录名一致；frontmatter 以 Agent Skills 开放标准字段为主，宿主扩展字段须在 description / 正文写明等效文字约束（见 AGENTS.md「维护约定」）。
- 组织侧同步副本（如 claude.ai 组织技能库上传过本仓库技能）**不随 git 更新**：基线变更后需重新上传或移除旧副本，否则与仓库形成双源漂移，且会在所有项目的会话里与项目安装副本并存。
- 校验：`bash scripts/verify-baseline.sh <目标项目根> [--show-diff] [--strict]`（自动识别目标的两种技能布局与前/后端仓）。
- 文件校验通过 ≠ 自动触发已实测：从目标项目启动新会话，用"今天做什么"、真实开发与审查请求验证路由。

---

> 团队 Vibe Coding 的总能力池：研发流程、前后端规范、审查硬流程、沉淀体系全部在此维护。
> 新项目直接引入即获得全部历史沉淀；项目中的新沉淀定期**反哺**回本仓库。
>
> **当前基线**：`2026-10-29`（重大流程变更时更新；引入项目记录此版本以便对齐校验）。
> **适用宿主**：任意 AI 编码宿主——Claude Code 按 `.claude/` 自动加载，其他宿主经 AGENTS.md 显式加载 `common/`。流程方法论 skill **与技术栈无关**
> （dev-session / pre-dev-alignment / progress-tracker / team-memory / capability-registry /
> similar-issue-sweep / dev-output / iteration-planner / project-onboarding / git-commit），任意项目可直接用；
> **栈相关 skill**（`yzj-dev-workflow`、`api-contract-checker`、`backend/*` = YZJ 四层 + MyBatis-Flex、
> `frontend/*` = Vue 3 + Naive UI）需同栈才适用——异栈项目取流程层，按 `skill-creator` 自建规范层。

---

## 一、仓库结构

```
skills/
├── common/skills/           # 通用能力（装到目标项目根的技能目录）
│   ├── dev-session/         #   研发生命周期编排（12 阶段 + 门禁 + 全程规则）★ 总入口
│   ├── pre-dev-alignment/   #   开发前对齐（前后端统一版 + 结论落档）
│   ├── iteration-planner/   #   迭代规划（session 开局对齐上下文）
│   ├── progress-tracker/    #   进度维护（STATUS.md 台账 + 任务清单回填 DoD + backlog 落档）
│   ├── team-memory/         #   团队记忆体系（纠正即沉淀硬规则）
│   ├── capability-registry/ #   能力登记册（复用前查册、沉淀后登记、反哺）
│   ├── similar-issue-sweep/ #   同类问题回溯扫描（修复必回溯）
│   ├── api-contract-checker/#   前后端契约校验（5 条规则）
│   ├── dev-output/          #   开发成果报告
│   ├── yzj-dev-workflow/    #   YZJ 后端开发流程总入口
│   ├── project-onboarding/  #   引入/融入向导（新项目初始化 + 既有项目对比合并）★
│   ├── git-commit/          #   Git 提交与分支规范（分支门禁 + feat/opt/fix + 无 AI 记号/进度词 + 安全暂存 + Worktree 附录）★
│   ├── neat-freak/          #   知识与规范收尾（文档/规则/记忆对齐现状，跨宿主，含审计脚本）
│   └── skill-creator/       #   技能创建与评测
├── backend/                 # 后端能力（装到后端仓库的技能目录）
│   ├── reviewer/            #   后端审查（七步硬流程 + 安全/金融/测试维度 + 55 条禁止清单 + 复查模式 + 漏检史）★
│   ├── project-structure / model-conventions / service-conventions
│   ├── controller-conventions / integration-flow / mybatis / cache
│   ├── security / common / logging / database-design / grpc / framework-usage
│   ├── financial/           #   金融级规范（BigDecimal / 幂等 / 事务 / 行锁 / 流水 / 脱敏）★
│   ├── testing/             #   单元测试规范（命名 / 模板 / 必测场景 / 禁止项 / 覆盖率）
│   ├── tabledef/            #   TableDef 手写维护规范
│   └── db-migration/        #   SQL 迁移脚本生成（up + down）
├── frontend/                 # 前端能力（装到前端仓库的技能目录）
│   ├── reviewer/            #   前端审查（七步硬流程 + 契约/i18n/token 扫描）★
│   ├── view-conventions/    #   页面开发规范（Vue 3 + Naive UI CRUD 模式）
│   └── i18n-automation/     #   i18n 自动化（补齐/校验/硬编码审计 + 脚本）
├── templates/               # 新项目引入模板
│   ├── CLAUDE.md.template   #   Claude Code 项目根入口骨架
│   ├── AGENTS.md.template   #   其他宿主项目入口骨架（含「执行门禁」）
│   ├── common/rules/        #   常驻规则模板（collaboration 协作原则 / api-contract 契约速查）
│   └── .document/           #   项目文档目录骨架（plan/STATUS.md + backlog、design、memory、capability、adr）
└── scripts/                 # 工具脚本
    └── verify-baseline.sh   #   校验项目 skill 与基线对齐（布局无关，自动识别前/后端与两种技能布局）
```

---

## 二、引入 / 融入项目

**推荐让 AI 执行 `project-onboarding` skill**：在能同时访问本仓库与目标项目的会话里，说
"把这套规范引入到 {项目路径}" / "旧项目融入这套流程"，AI 自动识别项目结构、区分新建 / 既有、拷贝对应 skill、
实例化 CLAUDE.md、补 `.document/` 骨架；既有项目按基线对比合并并保留项目专有沉淀。
**接入分两段**（project-onboarding 第二步门禁）：先**只读 dry-run 预演**——基线对比、漂移构成判读、动作清单、
报告落本仓库 `reports/{日期}-{项目}-onboarding-dryrun.md`——开发者确认动作清单后才正式落盘，落盘后按报告预期复验。

手动步骤（也是对 AI 流程的核对清单）：

```
（Claude Code 项目；其他宿主把 1/2 的目标换成 {project}/common/skills 与 {project}/common/rules，
  第 6 步改用 templates/AGENTS.md.template，详见顶部「接入方式」与 project-onboarding）
1. 拷贝通用能力 →  {project}/.claude/skills/        ← 本仓库 common/skills/*
2. 拷贝常驻规则 →  {project}/.claude/rules/         ← 本仓库 templates/common/rules/*（契约占位符按项目填）
3. 拷贝后端能力 →  {project}/{backend}/.claude/skills/   ← 本仓库 backend/*
4. 拷贝前端能力 →  {project}/{frontend}/.claude/skills/  ← 本仓库 frontend/*
5. 拷贝文档骨架 →  {project}/.document/             ← 本仓库 templates/.document/*
6. 用 templates/CLAUDE.md.template 建项目根 CLAUDE.md，填好占位符；加载引用一律相对路径
   （仓库路径、构建命令、设计系统 token 前缀；契约速查表填在 rules/api-contract.md）
7. 首次会话验证：说"今天做什么" → 应触发 iteration-planner 读取台账与计划
```

> **既有项目融入不是无脑覆盖**：流程 skill 按基线对齐；`reviewer` 与项目专有 skill **合并保留**项目沉淀（漏检史、项目注解、设计 token、命名规则）；项目独有 skill 不动。详见 `project-onboarding`「既有项目对比融入」。

> Claude Code 按**当前工作目录**加载对应 CLAUDE.md 与 skills，其他宿主按入口文件（AGENTS.md）声明的相对路径读取：项目根管流程，子仓库管前/后端规范。
> 引入后项目可在各自仓库追加**项目级 skill**（业务特定约定），通用部分演进后反哺回本仓库。

### 引入后验证清单（多项目通用 · 全绿才算"AI 能识别并执行"）

每个项目引入或同步后逐项确认；**B 组的 diff 是跨项目验证基线对齐的核心手段，已封装为 `scripts/verify-baseline.sh`**。

**A. 四件套就位（结构）**

```
- [ ] 项目根入口（CLAUDE.md / AGENTS.md）占位符全部替换，无残留 {xxx}；加载引用全部为相对路径
- [ ] 根常驻规则层（.claude/rules 或 common/rules）有 collaboration.md + api-contract.md（契约表与入口二选一，不重复维护）
- [ ] 根技能目录（.claude/skills 或 common/skills）有流程层；后端 / 前端仓库各有技能目录
- [ ] .document/ 含 plan/STATUS.md、design/、adr/、developer/memory + capability
- [ ] 每个 skill 的 name 与目录名一致（无 code-reviewer vs reviewer 类错位）
```

**B. 基线一致（版本）—— 多项目验证核心**

```
- [ ] 流程 skill 与本仓库当前版逐字一致：
      diff --strip-trailing-cr {项目技能目录}/{skill}/SKILL.md {framework}/common/skills/{skill}/SKILL.md  → 空
- [ ] reviewer / 规范 skill = 基线 + 项目专有项（diff 差异仅漏检史 / 项目注解 / 设计 token / 命名规则）
- [ ] 流程 skill 带项目专有硬约束的，差异仅为「📌 项目覆写」标记段，且文件头有差异清单（`project-onboarding`「📌 覆写约定」）
- [ ] 项目 CLAUDE.md 顶部记录引入时的 framework 基线（commit 短号或日期），落后于「当前基线」即提示 re-sync
```

**C. AI 能识别并触发（行为）**

```
- [ ] 新会话说"今天做什么" → 触发 iteration-planner，读到 STATUS.md
- [ ] 说"开发 XX" → 触发 dev-session（P1 定级 + 变更分级），L2/L3 走编码前文档门禁
- [ ] 任意编码后 → 自动跑 reviewer 七步硬流程（输出 echo 协议确认句）
- [ ] 后端业务开发 → 触发 yzj-dev-workflow + 对应 backend 子 skill
```

> 任一项不过 → 回 `project-onboarding` 对应步骤补齐。
>
> **一键校验**：`bash scripts/verify-baseline.sh {项目根}`（framework 省略时取本仓库）。它**按标志文件自动识别项目的前/后端仓库布局**（不依赖目录名，支持分仓 / mono-repo / 单栈），逐 skill 输出 `✓ 一致 / Δ 流程漂移 / 📌 项目覆写 / ℹ 项目专有差异 / ⊘ 项目专有 / ✗ 结构错误`，并查 frontmatter `name`/`description` 必备且 `name` 与目录名一致、root 流程 skill 按**已启用宿主布局逐一**齐全、**各端 reviewer 必备**（已装某端规范而缺 reviewer 即报错）、**前后端规范不得同目录混装**、基线路径有效（含空基线哨兵检查）、常驻规则层（`.claude/rules` 或 `common/rules`）是否就位（软提示）；项目覆写按 frontmatter 后 20 行内的「本文件 = framework 基线」引用块声明识别。单栈项目（根目录即前/后端仓）按根级**本级标志**（pom.xml / src/views 等）消歧，允许根技能目录混放通用 + 单端规范；含子仓的公共根只认纯 root。可在各项目本地 / CI 定期跑，实现多项目持续校验。加 `--show-diff` 看差异、`--strict` 让流程漂移即失败。

---

## 三、核心研发流程

所有开发任务统一走 `dev-session` 12 阶段：

```
P1 分析需求(读台账+定级) → P2 加载沉淀(memory+能力册) → P3 开发(文档产出+评审门禁→编码)
→ P4 AI Review(前后端 reviewer 硬流程+回溯扫描) → P5 自测
→ P6 开发者 Review(ARCH 深评/NORMAL 知会) → P7 开发者测试 → P8 确认
→ P9 更新进度(台账硬门禁) → P10 沉淀核对 → P11 提交 → P12 成果报告
```

**P3 编码前文档分层与门禁**（按 `pre-dev-alignment` 任务分级）：

- **L2** → 输出**技术设计文档**（`design/`），交**开发者**技术审核 + 二次评估，通过才编码
- **L3** → 先输出**需求/调整文档**（`plan/`）交**用户**复核对齐，再输出**技术设计文档**（`design/`）交**开发者**技术审核 + 二次评估，通过才编码
- **视觉交互 DEMO（按需）** → 用户要求视觉方案 / 全新无参照视觉时，产出 `design/{slug}-demo.html` 或复用前端既有组件做 DEMO，定稿后判断是否抽为复用组件并登记 `CAPABILITY.md`
- **联动需求契约先冻结** → 接口列表设计完先停一次确认，写入技术设计文档「契约」章节（接口列表 / Request-Response / 前端对接映射 / 错误码提示 / 不可改与敏感字段）；契约变更**先改文档再改两端实现**
- **砍范围必落 backlog** → 对齐中推迟 / 砍掉的功能点当场落 `plan/backlog-{topic}.md`（可独立阅读，下次对齐直接用），台账只放指针

**P11 提交与分支门禁**（按 `git-commit`）：

- 开发者授权（含笼统的"允许 / 提交吧"）**默认** = 从当前主干切开发分支 `{feat|opt|fix}/{yyyy.MM.dd}-{business}`
  （如 `feat/2026.08.18-edit-password`）→ 提交 → `push -u origin` → **由开发者自行合并主干**
- **已在开发分支**（名字合规）→ 原地提交推送，无需额外授权
- **主干直提**须开发者本次明确说"允许直接从主干提交"，**单次有效、下次必须重问、禁止 AI 自主判断**，且不得沉淀为常驻规则
- **暂存只加自己的改动**：逐项 `git add -- <路径>` + `git diff --cached --name-only` 核对；共享文件只暂存自己的 hunk；commit 与注释无 AI 记号、无进度词（FIXED / Step / Phase）
- **并行会话多时开 Worktree**（`git-commit` 附录）：放项目根 `.worktree/{business}/{repo}`，进度与沉淀只写根 `.document/`，Windows 后端仓先开 `core.longpaths`
- AI 一律不做：合并主干 / 开合 PR·MR / `push --force` / 删分支 / `git add -A`·`git commit -am` 盲加

**全程规则**（凌驾于单阶段）：

| 规则 | 内容 | 对应 skill |
|------|------|-----------|
| 纠正即沉淀 | 开发者纠正 → 修正后**立即**写 feedback memory，不等收尾 | `team-memory` |
| 修复必回溯 | 修一处 → 全库扫同类，一并修复或列清单 | `similar-issue-sweep` |
| 进度实时更新 | 状态迁移当下改台账，台账是并行开发唯一可信源；任务清单回填 DoD（完成 `[x]` / 废弃 `[⛔]`），提交前清单与代码一致 | `progress-tracker` |
| P4 不可跳过 | 任何编码后必过 reviewer 硬流程，"改动小"不是理由 | 前后端 `reviewer` |

**变更分级**（开发者注意力分配）：

- **ARCH 架构级**（架构/数据模型/安全/跨域/契约/不可逆）→ 开发者深度评审 + 测试 + 确认
- **NORMAL 常规级**（普通需求迭代）→ AI 严格自审，开发者知会式过目即可
- 拿不准按 ARCH；NORMAL 漏检被捕获 → 沉淀 + 同类变更升级 ARCH

---

## 四、设计依据（来自 YAPD 项目实战复盘）

| 实战痛点 | 本仓库的对策 |
|----------|--------------|
| 纠正过的问题没沉淀，重复犯错返工 | `team-memory` 纠正即沉淀硬规则 + 重复犯错升级机制（进 reviewer 漏检史） |
| 修一处不回溯同类，靠开发者查漏补缺 | `similar-issue-sweep` + dev-session 规则 2 + reviewer 同类违规回溯 |
| 规范明确却频繁违规、选择性 Review | 前后端 `reviewer` 七步硬流程：echo 协议、强制 Grep 扫描、逐维度×逐文件矩阵、漏检史必查 |
| 需求完成后进度不更新，后续误判 | `progress-tracker` STATUS.md 台账 + P9 硬门禁（不更新台账不算完成）+ 并行需求可见 |
| 技能/能力沉淀在各项目，复用率低 | `capability-registry` 复用前查册 + 待反哺区 + 本仓库作为总能力池 |
| 决策都做了但文档输出差 | `pre-dev-alignment` 对齐结论落档（需求文档→plan + 技术设计文档→design + 台账 + ADR），口头对齐不落档 = 未对齐 |
| 需求评审与技术评审混在一份、视觉方案靠口头想象 | L2/L3 **文档分层**：需求/调整文档(用户复核) 与 技术设计文档(开发者技术审核 + 二次评估) 分两道门禁；视觉方案按需出 HTML / 复用组件 DEMO |
| 开发者陷在逐行 review 中 | dev-session 变更分级：ARCH 深评 / NORMAL 知会，开发者专注方向与架构 |
| 并行会话互相污染工作区、进度在多棵树间分叉 | `git-commit` 安全暂存（逐项 add + 暂存区核对 + hunk 级）+ Worktree 附录（放项目根、进度只写根 `.document/`、树内命令以树内仓为 cwd、个人 memory 不跨树） |
| 多会话同写台账 / 索引后写覆盖，合并时不知保留谁 | `progress-tracker`「并行开发的文档冲突约定」：写前重读 / 只改自己的行 / 写完即提交；追加型双方保留；结构化文档归台账负责人独写；根非 git 仓时被覆盖就重写自己的行 |
| 任务清单失真（已做标未做、已回滚标已完成）、砍掉的范围被遗忘 | `progress-tracker` 回填 DoD + `[⛔]` 已废弃 + backlog 文档（推迟即落档） |
| 全栈契约靠口头，后端先改实现再补文档 | 技术设计文档「契约」章节冻结 + 联动需求接口确认停顿点 + 契约变更先改文档 |
| 项目专有覆写散落在正文，re-sync 时被基线冲掉 | `project-onboarding`「📌 覆写约定」（文件头差异清单 + 行内标记）+ verify-baseline 按文件头声明识别覆写 |
| 协作底线只写在 skill 里、按需才加载 | `templates/common/rules/` 常驻规则（冲突处理 / 刹车点 / 纠正 vs 妥协 / 执行自证 / 契约速查），Claude Code 自动加载、其他宿主经 AGENTS.md 显式引用 |
| 后端规范没有金融、安全编码、测试维度，reviewer 十个维度里没有安全 | `backend/financial` + `security` 第八节红线 + `backend/testing`；reviewer 新增安全 / 金融 / 测试维度、HIGH RISK 升级（🟡 视同 🔴 + 双人审批）、ARCH 级复查模式 |
| 框架日志过滤器默认打全量 body，"业务不打敏感日志"被误当成"敏感数据不入日志" | `logging` 第九节：`LoggerFilter` 忽略清单作为接口 DoD、逐层各配、逐层验证；reviewer 漏检史登记 |
| 对外接口先改实现后补文档，第三方按旧文档对接 | reviewer #48：对外接口 / SDK / proto 变更的对接文档必须同一次提交更新 |

---

## 五、反哺流程（项目 → framework）

1. 项目开发中，可复用产出按 `capability-registry` 登记，跨项目通用的进「待反哺 framework」区
2. 迭代间歇做通用化改造（去项目专有命名/路径/业务假设）
3. 按归属落位：流程方法论 → `common/skills/`；后端规范 → `backend/`；前端规范 → `frontend/`
4. 提交本仓库：`feat(capability): 反哺 {能力} from {项目}`
5. 项目登记册标记 `已反哺`；其他项目拉取更新即可受益

**项目侧技能与本仓库的同步**：项目内拷贝的 skill 发生演进（规则更新、漏检史追加）时，通用部分应同步回本仓库，项目专有部分留在项目副本——以本仓库为基线，项目副本只增不删。

---

## 六、维护约定

- 每个 skill 一个目录，入口 `SKILL.md`（frontmatter：`name` + 触发场景写入 `description`）
- 修改流程类 skill（dev-session / reviewer / progress-tracker）需团队过目——它们是所有项目的执行协议
- 新增 skill 用 `skill-creator` 创建并评测；提交与分支遵循 `git-commit` skill（授权后切 `{feat|opt|fix}/{yyyy.MM.dd}-{business}` 开发分支提交并推送、开发者自行合并主干；feat/opt/fix 三分法，scope 可选，禁止 AI 记号）
- 重大流程变更（dev-session / reviewer / 文档门禁 / 契约规则）→ 更新本 README 顶部「当前基线」日期；各引入项目据此判断是否需 re-sync（用「引入后验证」B 组 diff 确认）
- 项目副本对流程 skill 的专有覆写按「📌 覆写约定」标记（文件头差异清单 + 行内 📌），不散改正文；主干直提、跳过 P4、P8 确认之类的门禁不得被覆写放宽
