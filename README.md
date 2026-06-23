# YZJ 团队共享技能库（skills）

> 团队 Vibe Coding 的总能力池：研发流程、前后端规范、审查硬流程、沉淀体系全部在此维护。
> 新项目直接引入即获得全部历史沉淀；项目中的新沉淀定期**反哺**回本仓库。
>
> **当前基线**：`2026-06-23`（重大流程变更时更新；引入项目记录此版本以便对齐校验）。
> **适用前提**：Claude Code（按工作目录加载 CLAUDE.md + skills）。流程方法论 skill **与技术栈无关**
> （dev-session / pre-dev-alignment / progress-tracker / team-memory / capability-registry /
> similar-issue-sweep / dev-output / iteration-planner / project-onboarding），任意项目可直接用；
> **栈相关 skill**（`yzj-dev-workflow`、`api-contract-checker`、`backend/*` = YZJ 四层 + MyBatis-Flex、
> `frontend/*` = Vue 3 + Naive UI）需同栈才适用——异栈项目取流程层，按 `skill-creator` 自建规范层。

---

## 一、仓库结构

```
skills/
├── .claude/skills/          # 通用能力（项目根 .claude/skills/）
│   ├── dev-session/         #   研发生命周期编排（12 阶段 + 门禁 + 全程规则）★ 总入口
│   ├── pre-dev-alignment/   #   开发前对齐（前后端统一版 + 结论落档）
│   ├── iteration-planner/   #   迭代规划（session 开局对齐上下文）
│   ├── progress-tracker/    #   进度维护（STATUS.md 需求台账 + 并行开发）
│   ├── team-memory/         #   团队记忆体系（纠正即沉淀硬规则）
│   ├── capability-registry/ #   能力登记册（复用前查册、沉淀后登记、反哺）
│   ├── similar-issue-sweep/ #   同类问题回溯扫描（修复必回溯）
│   ├── api-contract-checker/#   前后端契约校验（5 条规则）
│   ├── dev-output/          #   开发成果报告
│   ├── yzj-dev-workflow/    #   YZJ 后端开发流程总入口
│   ├── project-onboarding/  #   引入/融入向导（新项目初始化 + 既有项目对比合并）★
│   └── skill-creator/       #   技能创建与评测
├── backend/                 # 后端能力（后端仓库 .claude/skills/）
│   ├── reviewer/            #   后端审查（七步硬流程 + 40 条禁止清单 + 漏检史）★
│   ├── project-structure / model-conventions / service-conventions
│   ├── controller-conventions / integration-flow / mybatis / cache
│   ├── security / common / logging / database-design / grpc / framework-usage
│   ├── tabledef/            #   TableDef 手写维护规范
│   └── db-migration/        #   SQL 迁移脚本生成（up + down）
├── frontend/                 # 前端能力（前端仓库 .claude/skills/）
│   ├── reviewer/            #   前端审查（七步硬流程 + 契约/i18n/token 扫描）★
│   ├── view-conventions/    #   页面开发规范（Vue 3 + Naive UI CRUD 模式）
│   └── i18n-automation/     #   i18n 自动化（补齐/校验/硬编码审计 + 脚本）
├── templates/               # 新项目引入模板
│   ├── CLAUDE.md.template   #   项目根 CLAUDE.md 骨架
│   └── .document/           #   项目文档目录骨架（plan/STATUS.md、design、memory、capability、adr）
└── scripts/                 # 工具脚本
    └── verify-baseline.sh   #   校验项目 skill 与基线对齐（布局无关，自动识别前/后端）
```

---

## 二、引入 / 融入项目

**推荐让 AI 执行 `project-onboarding` skill**：在能同时访问本仓库与目标项目的会话里，说
"把这套规范引入到 {项目路径}" / "旧项目融入这套流程"，AI 自动识别项目结构、区分新建 / 既有、拷贝对应 skill、
实例化 CLAUDE.md、补 `.document/` 骨架；既有项目按基线对比合并并保留项目专有沉淀。

手动步骤（也是对 AI 流程的核对清单）：

```
1. 拷贝通用能力 →  {project}/.claude/skills/        ← 本仓库 .claude/skills/*
2. 拷贝后端能力 →  {project}/{backend}/.claude/skills/   ← 本仓库 backend/*
3. 拷贝前端能力 →  {project}/{frontend}/.claude/skills/  ← 本仓库 frontend/*
4. 拷贝文档骨架 →  {project}/.document/             ← 本仓库 templates/.document/*
5. 用 templates/CLAUDE.md.template 建项目根 CLAUDE.md，填好占位符
   （仓库路径、构建命令、设计系统 token 前缀、契约约定）
6. 首次会话验证：说"今天做什么" → 应触发 iteration-planner 读取台账与计划
```

> **既有项目融入不是无脑覆盖**：流程 skill 按基线对齐；`reviewer` 与项目专有 skill **合并保留**项目沉淀（漏检史、项目注解、设计 token、命名规则）；项目独有 skill 不动。详见 `project-onboarding`「既有项目对比融入」。

> Claude Code 按**当前工作目录**加载对应 CLAUDE.md 与 skills：项目根管流程，子仓库管前/后端规范。
> 引入后项目可在各自仓库追加**项目级 skill**（业务特定约定），通用部分演进后反哺回本仓库。

### 引入后验证清单（多项目通用 · 全绿才算"AI 能识别并执行"）

每个项目引入或同步后逐项确认；**B 组的 diff 是跨项目验证基线对齐的核心手段，已封装为 `scripts/verify-baseline.sh`**。

**A. 三件套就位（结构）**

```
- [ ] 项目根 CLAUDE.md 占位符全部替换，无残留 {xxx}
- [ ] 根 .claude/skills/ 有流程层；后端 / 前端仓库各有 .claude/skills/
- [ ] .document/ 含 plan/STATUS.md、design/、adr/、developer/memory + capability
- [ ] 每个 skill 的 name 与目录名一致（无 code-reviewer vs reviewer 类错位）
```

**B. 基线一致（版本）—— 多项目验证核心**

```
- [ ] 流程 skill 与本仓库当前版逐字一致：
      diff --strip-trailing-cr {项目}/.claude/skills/{skill}/SKILL.md {framework}/.claude/skills/{skill}/SKILL.md  → 空
- [ ] reviewer / 规范 skill = 基线 + 项目专有项（diff 差异仅漏检史 / 项目注解 / 设计 token / 命名规则）
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
> **一键校验**：`bash scripts/verify-baseline.sh {项目根}`（framework 省略时取本仓库）。它**按标志文件自动识别项目的前/后端仓库布局**（不依赖目录名，支持分仓 / mono-repo / 单栈），逐 skill 输出 `✓ 一致 / Δ 流程漂移 / ℹ 项目专有差异 / ⊘ 项目专有 / ✗ 结构错误`，并查 `name` 与目录名是否一致、root 流程 skill 是否齐全。可在各项目本地 / CI 定期跑，实现多项目持续校验。加 `--show-diff` 看差异、`--strict` 让流程漂移即失败。

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

**全程规则**（凌驾于单阶段）：

| 规则 | 内容 | 对应 skill |
|------|------|-----------|
| 纠正即沉淀 | 开发者纠正 → 修正后**立即**写 feedback memory，不等收尾 | `team-memory` |
| 修复必回溯 | 修一处 → 全库扫同类，一并修复或列清单 | `similar-issue-sweep` |
| 进度实时更新 | 状态迁移当下改台账，台账是并行开发唯一可信源 | `progress-tracker` |
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

---

## 五、反哺流程（项目 → framework）

1. 项目开发中，可复用产出按 `capability-registry` 登记，跨项目通用的进「待反哺 framework」区
2. 迭代间歇做通用化改造（去项目专有命名/路径/业务假设）
3. 按归属落位：流程方法论 → `.claude/skills/`；后端规范 → `backend/`；前端规范 → `frontend/`
4. 提交本仓库：`feat(capability): 反哺 {能力} from {项目}`
5. 项目登记册标记 `已反哺`；其他项目拉取更新即可受益

**项目侧技能与本仓库的同步**：项目内拷贝的 skill 发生演进（规则更新、漏检史追加）时，通用部分应同步回本仓库，项目专有部分留在项目副本——以本仓库为基线，项目副本只增不删。

---

## 六、维护约定

- 每个 skill 一个目录，入口 `SKILL.md`（frontmatter：`name` + 触发场景写入 `description`）
- 修改流程类 skill（dev-session / reviewer / progress-tracker）需团队过目——它们是所有项目的执行协议
- 新增 skill 用 `skill-creator` 创建并评测；提交信息遵循 `type(scope): 简述`
- 重大流程变更（dev-session / reviewer / 文档门禁 / 契约规则）→ 更新本 README 顶部「当前基线」日期；各引入项目据此判断是否需 re-sync（用「引入后验证」B 组 diff 确认）
