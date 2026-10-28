---
name: git-commit
description: >
  Git 提交与分支规范（团队通用）。定义提交前的分支门禁——授权提交默认「从当前主干切
  {feat/opt/fix}/{yyyy.MM.dd}-{business} 开发分支 → 提交 → 推送 → 交开发者自行合并主干」，
  主干直提须开发者单次明确授权且永不继承；并定义 feat/opt/fix 三类前缀、header/body 书写格式、
  多类型合并写法，以及"AI 自主编写提交信息、commit 中不得留任何 AI 记号与进度词"等铁律；
  另定义并行开发下只提交自己改动的安全暂存细则、多仓交接对照，以及 Worktree 隔离开发指引。
  当需要提交代码、编写 commit message、切开发分支、推送分支、在并行会话下安全暂存、开 worktree 隔离开发，
  开发者说"提交吧"/"允许"/"帮我 commit"/
  "你来提交代码"/"直接提交"/"允许直接从主干提交"/"git commit"/"git push"，
  或 dev-session 进入 P11 提交阶段时触发；dev-session P11 自动引用。
---

# Git 提交与分支规范（git-commit）

> 提交历史是团队读得最多的文档之一：规范的 commit 让 diff 可追溯、让每次改动的"为什么"一眼可见；
> 规范的分支让主干始终可发布、让合并权始终握在开发者手里。
> 本 skill 定义三件事——**提交前的分支门禁**、**AI 被授权提交时的三条铁律**、**feat/opt/fix 三类前缀 + 书写格式**；
> 附录给出**并行开发的安全暂存**与 **Worktree 隔离开发**的固定做法。

---

## 一、AI 自主提交：授权与三条铁律

### 触发授权（前置门禁）

仅当**开发者明确授权**时才执行 `git commit`：如 dev-session P8 确认提交，或开发者说
"允许 / 你提交吧 / 帮我 commit / 直接提交 / 你来写提交信息"。未获授权只准备好变更并展示，不自行提交。

> **"允许"的默认含义 = 走第二章的分支流程**（切开发分支 → 提交 → 推送），**不等于**允许在主干提交。

### 铁律 1 — 提交必须落在开发分支 ← 硬性

除开发者**本次明确**说"允许直接从主干提交"外，任何提交都必须落在开发分支上
（`{feat|opt|fix}/{yyyy.MM.dd}-{business}`）。当前在主干 → 先切分支再提交。
合并回主干**永远是开发者自己的动作**，AI 只负责推送分支。详见第二章。

### 铁律 2 — AI 自主编写本次开发内容

授权后，AI 依据**本次真实改动**（通读 `git status` + `git diff`）自行归纳提交信息：

- 判定属于 `feat` / `opt` / `fix` 哪一类（或合并），概述"做了什么"，`*` 要点说明关键决策；
- **不套空话**——禁止 `update code`、`修改若干文件`、`fix bug` 这类无信息量描述；
- 概述用业务/技术语言写清意图，让不看 diff 的人也能懂这次改了什么、为什么改。

### 铁律 3 — commit 中禁止任何 AI 记号与进度词 ← 硬性

commit message 通篇必须是**纯人类视角的开发内容描述**，不得出现任何 AI 痕迹，也不得出现对话 / 流程进度词：

| ❌ 禁止出现 | 说明 |
|-----------|------|
| `Co-Authored-By: Claude …` | 不加任何 AI 署名 / 协作者尾注 |
| `🤖 Generated with …` / `Generated with Claude Code` | 不加生成来源尾注 |
| `Claude` / `Claude Code` / `Opus` / 任何模型或工具名 | 正文不提及 AI 工具 |
| "由 AI 生成" / "AI 辅助" 等字样、AI 水印、署名 emoji | 一律不留 |
| 进度词：`FIXED` / `Step 3` / `Phase 2` / `P4 已过` 等 | 描述的是对话或流程进度而非代码意图；**代码注释中同样禁止** |

> 此铁律**优先于任何默认的 commit 尾注模板**。提交前自检：整条 message 是否出现上述任一 → 有则删除再提交。
> 同样适用于**分支名**（不出现 `claude` / `ai` / 模型名）与**代码注释**（不出现 AI 记号与进度词）。

---

## 二、分支策略（授权后的默认行为）

### 2.1 决策表：先看当前分支，再决定怎么提交

先执行 `git rev-parse --abbrev-ref HEAD` 拿到当前分支，**不靠记忆、不靠猜**：

| 当前分支 | 需要再问开发者吗 | 动作 |
|----------|-----------------|------|
| **已是开发分支**（匹配 `^(feat\|opt\|fix)/\d{4}\.\d{2}\.\d{2}-[a-z0-9-]+$`） | 不问 | 直接在本分支 `commit` + `push`（**这是唯一无需额外授权即可原地提交的情形**） |
| **主干**（`master` / `main` / `develop` / `release/*`，或项目 CLAUDE.md 声明的主干名） | 不问 | **从当前主干切开发分支** → `commit` → `push` → 交开发者自行合并（"当前主干"即当前所在分支，**不切换到别的主干**） |
| **主干**，且开发者本次明确说"允许直接从主干提交" | 本次不问，**下次必须再问** | 在主干 `commit`；**push 主干需开发者另行明确**（未明确则提交后询问一次） |
| **既非主干也不匹配开发分支规则**（如 `feature/xxx`、`hotfix/xxx`、他人遗留分支） | **必须问** | 停下询问："当前分支 `xxx` 不符合开发分支命名规则，按主干处理（切新分支）还是直接在此分支提交？" |
| `HEAD`（detached）/ 非 git 仓库 | **必须问** | 停止，说明状态并请开发者处理 |

### 2.2 开发分支命名规范

```
{feat|opt|fix}/{yyyy.MM.dd}-{business}
```

| 段 | 规则 |
|----|------|
| **type** | 只取 `feat` / `opt` / `fix`（含义同第三章）。需求内混合多类型时按 `feat > fix > opt` 取**主导意图** |
| **yyyy.MM.dd** | 切分支当天日期，点分隔、月日补零（`2026.08.18`）。**执行命令取当天日期，不凭记忆填**：`date +%Y.%m.%d`（Windows PowerShell：`Get-Date -Format 'yyyy.MM.dd'`） |
| **business** | 需求业务名，小写英文 kebab-case，2–4 个词，见名知意；中文需求译成英文（修改密码 → `edit-password`；订单导出 → `order-export`） |

**示例**

```
feat/2026.08.18-edit-password        # 修改密码需求
feat/2026.08.18-finance-report       # 财务报表模块
opt/2026.08.18-batch-import          # 批量导入优化
fix/2026.08.18-order-remark-npe      # 确认订单备注 NPE
```

**反例**

| ❌ 分支名 | 问题 |
|----------|------|
| `feat/2026.8.18-edit-password` | 月日未补零 |
| `feat/2026.08.18-editPassword` | business 用了驼峰，应 kebab-case |
| `feat/edit-password` | 缺日期段 |
| `feature/2026.08.18-edit-password` | 前缀不在 `feat/opt/fix` 三类内 |
| `feat/2026.08.18-fix-bug` | business 无信息量，看不出改了什么业务 |

> **同一需求延续开发沿用原分支**：不因跨天而按新日期另开分支；也不因某次改动类型不同（在 `feat` 分支上修了个 bug）而改分支名——分支名跟**需求主导意图**，commit 前缀跟**每次改动意图**。
>
> **同一业务需要重开分支**（原分支已合并 / 已废弃，同一 business 要再开一支）：沿用原分支名**追加序号** `-2`、`-3`（如 `opt/2026.08.03-sub-code-config-2`），日期与 business 都不改——序号让人一眼看出这是同一需求的第几轮，不会误当成新需求。

### 2.3 默认流程（授权后逐步执行）

1. **确认状态**：`git status` + `git diff` 通读本次全部改动；`git rev-parse --abbrev-ref HEAD` 判定当前分支（→ 2.1 决策表）
2. **切分支**（当前在主干时）：
   - 可选先 `git fetch`，若当前主干落后远端，**如实告知开发者**，是否 `pull` / `rebase` 由开发者决定——**AI 不自动拉取或变基**（工作区有未提交改动时风险最大）
   - `git switch -c {分支名}`（工作区未提交改动会随之带到新分支，无需 stash）
3. **暂存**：按 `git status` **逐项确认后**再 `git add -- <显式路径>`；**禁止 `git add -A` / `git add .` / `git commit -am` 盲加**（避免带入临时文件、他人改动、本地配置）；暂存后 `git diff --cached --name-only` 核对一遍再提交——工作区有他人 / 他任务改动时按 **2.4 安全暂存**执行
4. **提交**：`git commit` —— message 按第三、四章（三分法 + 格式 + **无 AI 记号**）
5. **推送**：`git push -u origin {分支名}`
6. **交接输出**（推送后给开发者的固定四项）：
   ```
   分支：feat/2026.08.18-edit-password（自 master 切出）
   提交：a1b2c3d  feat: 新增修改密码能力
   推送：已推送到 origin（远端返回的 PR/MR 链接，如有）
   待办：请自行合并到 master
   ```
7. **收尾**：`git status` 确认工作区干净

**多仓库（前后端 / 多服务）**：各仓库独立执行本流程、独立提交；**分支名保持一致**（同一需求同名分支，便于对照合并）；交接输出**逐仓列出**「仓库 ↔ 分支 ↔ 提交」对照，不能只报其中一个仓：

```
仓库：{backend-repo}   分支：feat/2026.08.18-edit-password   提交：a1b2c3d  已推送
仓库：{frontend-repo}  分支：feat/2026.08.18-edit-password   提交：d4e5f6a  已推送
待办：请自行合并两仓分支到 master
```

### 2.4 并行开发的安全暂存 ← 硬性

工作区可能含**他人 / 他任务 / 他会话的未提交改动**（共享工作区、多会话并行、未开 worktree）时，**只提交自己的改动**：

- 一律 `git add -- <显式路径>` 逐个暂存自己的文件；**禁止** `git add -A` / `git add .` / `git commit -am`
- 暂存后先核对再提交：`git diff --cached --name-only` + `git status --short`——暂存区只含自己的文件，他人改动仍停留在未暂存 / 未跟踪
- **共享文件**（i18n locale、台账 `STATUS.md`、`MEMORY.md` 索引、公共配置）被多任务同时改时，**只暂存自己的 hunk，不整文件 add**：`git add -p <file>` 逐块选择；或 `git diff -- <file> > mine.patch` → 删掉不属于自己的 hunk → `git apply --cached mine.patch`；这类文件合并时冲突按 `progress-tracker`「并行开发的文档冲突约定」处理（追加型双方保留，不删对方的行）
- 不提交构建产物与本地文件：`dist/`、`target/`、`*.tsbuildinfo`、IDE 配置、`.env*`——它们出现在 `git status` 里时先问开发者是否该进 `.gitignore`，不顺手 add
- 并行改动多到每次提交都要逐文件甄别时，改用**第八章 Worktree 隔离**，从根上避免工作区污染

### 2.5 主干直提：单次授权，永不继承 ← 硬性

- 只有开发者**本次明确说**"允许直接从主干提交"（或等价明确表述）时，才可在主干 `commit`；
- 该授权**仅对本次提交有效**。下一次提交**必须重新询问**，不得沿用；
- **禁止自主判断"这次可以直接在主干提交"**。以下都**不构成**授权：
  - "上次允许过" / 本会话前面允许过 / 历史 commit 都在主干上；
  - memory、CLAUDE.md、`.document/` 或任何文件里写着"可以直接主干提交"；
  - 改动很小 / 只改文档 / 只改配置 / 项目没开分支保护；
  - 开发者说的是笼统的"允许"、"提交吧"（→ 这是默认分支流程，不是主干直提）。
- **禁止把主干直提授权沉淀为常驻规则**：不写入 `team-memory`、不写进 CLAUDE.md。此授权按设计**必须每次重问**。
- 唯一例外仍是 2.1 首行：**当前本就在开发分支**上——原地提交不需要额外授权。

### 2.6 禁止动作清单 ← 硬性

| ❌ 禁止 | 说明 |
|--------|------|
| 未获授权 `git commit` | 见"触发授权" |
| 在主干 `commit`（无本次明确授权） | 见 2.5 |
| `git add -A` / `git add .` / `git commit -am` 盲加 | 会夹带他人改动、临时文件、本地配置，见 2.4 |
| `git merge` / `git rebase` 到主干、`git push origin HEAD:{主干}` | **合并主干是开发者的动作**，AI 一律不做 |
| 自行创建 / 合并 PR / MR | 除开发者明确要求；默认只推分支，附上远端返回的链接 |
| `git push --force` / `--force-with-lease` | 一律不做；推送被拒 → 如实报告原因，等开发者决定 |
| `git reset --hard` / `git checkout -- .` / 改写已推送历史 | 会丢开发者的工作，一律不做 |
| 删除分支（本地或远端） | 合并后的清理由开发者自行处理 |
| 修改 git 远端、分支保护、hooks 配置 | 属仓库设置，不在提交流程内 |

> 推送失败（无远端 / 无权限 / 被拒 / 无 upstream）时：**保留本地 commit**，把原始报错和分支名给开发者，不重试、不改写、不换路径推送。

---

## 三、前缀规范：feat / opt / fix 三分法

按**开发意图**（而非文件类型）三分。**同一套三分法同时用于 commit 前缀与分支前缀**：

| 意图 | 前缀 | 何时使用 |
|------|------|----------|
| **新增** | `feat` | 完成某个模块开发、业务的改造、需求的迭代；新增接口 / 页面 / 字段 / 能力 |
| **改进** | `opt` | 对代码进行优化、调整，或做简要的内容补充（重构、性能、格式、配置 / 依赖、文档与注释） |
| **修复** | `fix` | 修复某个 BUG / 缺陷 |

### 与既有六类的融合映射

本库过去在 dev-session P11 / README 隐性用过 `feat / fix / refactor / docs / style / chore` 六类。
现统一收敛到三类，旧类型按下表**逐类归入**——**三分法覆盖全部提交场景，不再使用其余前缀**：

| 旧前缀 | 归入 | 理由 |
|--------|------|------|
| feat | **feat** | 新增价值 |
| fix | **fix** | 补回正确性 |
| refactor / perf | **opt** | 不改变对外行为地改进内在质量 |
| style | **opt** | 格式 / 样式属"调整" |
| chore | **opt** | 构建 / 依赖 / 配置 / 杂务属"调整" |
| docs | **opt** | 文档 / 注释属"简要的内容补充"（opt 定义即含此） |

> 记忆法：**加东西 → feat，修东西 → fix，其余一切"让现状更好" → opt。**

---

## 四、书写格式

### 结构

```
<type>[(<scope>)]: <概述>[ & <概述2> …]

* <要点1>
* <要点2>
```

- **type**：`feat` / `opt` / `fix`
- **scope（可选）**：改动范围 / 模块，如 `(skills)`、`(capability)`、`(订单)`。
  本库自身提交与反哺提交带 scope；日常业务提交可省略。
- **概述**：一句话说清做了什么；一次提交含多件相关事项时用 ` & ` 连接。
- **body（`*` 要点，按需）**：解释关键实现决策 / 为什么这么改 / 影响面；无必要可省。

### 多类型合并

一次改动同时涉及新增、优化、修复时，按 `feat → opt → fix` 顺序分段，段间空行：

```
feat: <概述>

* <要点>

opt: <概述>

* <要点>

fix: <概述>

* <要点>
```

---

## 五、示例

**feat**

```
feat: 新增财务报表的导出接口 & 资金科目模块新增门店维度统计

* 统一导出工具类，支持读库自定义
```

**opt**

```
opt: 数据上报通知由同步改为异步 & 优化批量导入的逻辑

* 批量导入由 for 循环 saveOrUpdate 改为批量 saveOrUpdateBatch
```

**fix**

```
fix: 确认订单当没填写备注时出现 NPE & 商品导出表头没有国际化

* 确认订单要对 remark 字段做空判断
* 商品导出补充 commodity.name, commodity.price 国际化文案
```

**合并（feat + opt + fix）**

```
feat: 新增 XXX

* XXX

opt: 优化 XXX

* XXX

fix: 修复 XXX

* XXX
```

**带 scope（本库 / 反哺）**

```
feat(capability): 反哺 verify-baseline 校验脚本 from YAPD
```

**分支 + 提交配套（修改密码需求）**

```
分支：feat/2026.08.18-edit-password
提交：feat: 新增用户修改密码能力

* 旧密码校验走统一 PasswordEncoder，失败次数计入风控
```

---

## 六、提交流程（对接 dev-session P11）

1. `git status` + `git diff` 通读本次全部改动
2. 确认已获开发者提交授权（未授权 → 只展示变更，停）
3. **分支门禁**：`git rev-parse --abbrev-ref HEAD` → 按 2.1 决策表定动作（主干 → 切 `{type}/{yyyy.MM.dd}-{business}`）
4. 前后端仓库各自独立提交、分支名一致；`.document/` 变更（台账 / 报告 / memory）随同对应提交
5. 按本规范归类并编写 message（三分法 + 格式 + **无 AI 记号 / 无进度词**）
6. 逐项 `git add -- <显式路径>`（不盲加）→ `git diff --cached --name-only` 核对暂存区（并行开发按 2.4 只暂存自己的改动）→ `git commit`
7. `git push -u origin {分支名}` → 输出交接四项（分支 / 提交 / 推送 / 待办：请自行合并主干；多仓逐仓列对照）
8. `git status` 确认工作区干净

---

## 七、质量自检（提交前逐条过）

**分支**

- [ ] 已获开发者提交授权
- [ ] 已用 `git rev-parse --abbrev-ref HEAD` 确认当前分支，而非凭印象
- [ ] 当前不在主干；若在主干，已切出开发分支（**主干直提仅凭本次明确授权，且不沿用上次**）
- [ ] 分支名合规：`{feat|opt|fix}/{yyyy.MM.dd}-{business}`，日期取自系统当天且补零，business 为小写 kebab-case 且有信息量
- [ ] 前后端仓库分支名一致
- [ ] 未做任何合并主干 / PR / force push / 删分支动作

**暂存**

- [ ] 逐项 `git add -- <路径>`，未用 `-A` / `.` / `-am` 盲加
- [ ] `git diff --cached --name-only` 已核对：未夹带他人改动、构建产物、本地配置

**提交信息**

- [ ] 前缀 ∈ {`feat`, `opt`, `fix`}，与本次意图一致
- [ ] 概述具体、有信息量，不是 `update` / `修改代码` 这类空话
- [ ] 多事项用 ` & ` 连接；多类型按 `feat → opt → fix` 分段
- [ ] 关键决策已在 `*` 要点说明（如有必要）
- [ ] **message 与分支名中无任何 AI 记号**（`Co-Authored-By` / `Generated with` / 模型名 / AI 水印）
- [ ] **message 与代码注释中无进度词**（`FIXED` / `Step N` / `Phase N`）

**收尾**

- [ ] 已 `push -u origin {分支名}`，并向开发者输出交接四项（分支 / 提交 / 推送 / 待办：请自行合并主干）；多仓时逐仓列出「仓库 ↔ 分支 ↔ 提交」对照
- [ ] `git status` 工作区干净

---

## 八、附录：Worktree 隔离开发（并行迭代防冲突 / 防进度脱节）

> 同一仓库有另一会话 / 另一需求在并行改动时，三类事故反复发生：他人切分支清掉本需求**未提交**的 tracked 改动；每次提交都要在污染的工作区里逐文件甄别（2.4）；本需求改动混进他人分支。把本需求隔离到独立 `git worktree` 可以从根上避免。以下是实战踩坑后的固定做法。

### 8.1 何时用

- 共享工作区有活跃并行会话，且本需求是**多文件、多任务、会累积较多未提交改动**的特性
- 单文件 / 快速改动不开 worktree，按 2.4 安全暂存即可

### 8.2 放置位置与目录结构（强制）

worktree **必须放在项目根内** `{project-root}/.worktree/`，**不放项目外**——放外面会让项目根的入口与技能层（Claude Code：`.claude/` 流程 skill + rules；其他宿主：AGENTS.md 及其引用的技能目录）与 `.document/`（台账 / 沉淀）脱离祖先链，规则和 skill 加载 / 引用不到。

按「**任务目录镜像根结构**」组织：每个需求一个任务目录，内含该需求用到的各仓 worktree，**子目录名与项目根下的仓库目录名一致**：

```
{project-root}/.worktree/
└── {business}/                 ← 一个需求一个目录，与分支的 business 段同名（如 edit-password）
    ├── {backend-repo}/         ← 后端仓 worktree，检出 feat/2026.08.18-edit-password
    └── {frontend-repo}/        ← 前端仓 worktree，同名分支（按需）
```

- 建树命令：`git -C {repo} worktree add {project-root}/.worktree/{business}/{repo} -b {feat|opt|fix}/{yyyy.MM.dd}-{business}`（自当前主干切出，分支名按 2.2）
- worktree 是**单仓**检出：纯后端 / 纯前端只建对应那一个；全栈各建各的，互不影响
- 编辑任一仓文件时祖先链含：该仓技能层（前 / 后端规范）+ 根技能层（流程）+ 根 `.document/`（Claude Code 下技能层即各级 `.claude/`；其他宿主为入口文件声明的技能目录）→ 规则与技能全识别
- `.worktree/` 必须进项目根 `.gitignore`（单仓项目尤其注意，否则整棵树会被当成未跟踪文件）
- 多需求并行各用各的任务目录与分支（同一仓同一分支只能在一个 worktree 检出）
- **树内一切命令以树内仓目录为 cwd**：构建 / 测试 / 校验命令不用项目根相对路径——项目 CLAUDE.md 里 `cd {backend-repo} && mvn …` 这类命令在 worktree 会话里要按 `{project-root}/.worktree/{business}/{repo}` 解析，否则编译 / 测试的是主工作区那棵树；跨仓引用写 `../{repo}`，镜像结构保证它在根与树内都指向同一需求的另一棵树

### 8.3 Windows 路径上限（260）——后端仓必做

后端 Java 包路径深，嵌套一层任务目录后最深文件容易超过 Windows MAX_PATH。**建树前对该仓执行一次 `git config core.longpaths true`**，否则 `git worktree add` 报 `Could not reset index file to revision 'HEAD'`。开启后 git 与读写 / 编辑工具均能正常处理深路径文件。

### 8.4 进度与沉淀只写一份（关键）

- `.document/` 全项目只有项目根这一份：台账 `STATUS.md`、plan / design / 用例文档、memory、能力登记**一律写项目根**，**绝不写进 worktree 内的副本**——单仓项目的 worktree 会自带一份 `.document/` 副本，最容易写错地方 → 进度永不在多棵树间分叉
- 每完成一个任务**即时**按 `progress-tracker` 回填，并在 worktree 内**分段提交**（每个可独立 review 的语义单元一次），不长期囤大量未提交改动
- 开树时在台账该条目「最近动态」记一行：worktree 路径 + 分支名 + 所属仓，避免跨会话丢失上下文
- **个人 memory 不跨树**：个人 memory（Claude Code：`~/.claude/projects/`；其他宿主：用户配置的位置）按 cwd 路径分桶，worktree 会话与主工作区会话读到的不是同一份——需求上下文、纠正、踩坑一律按 `team-memory` 写根 `.document/developer/memory/`，不要靠个人 memory 在树之间传递
- **多会话同写根 `.document/`**（台账、索引、能力登记）→ 按 `progress-tracker`「并行开发的文档冲突约定」：写前重读、只改自己的行、写完即提交；追加型文件冲突双方保留；结构化文档单一写者

### 8.5 提交、合并与收尾

- 提交推送按 2.3 默认流程：在 worktree 内 `commit` → `push -u origin {分支名}` → 交接四项
- 基线漂移：主干推进较多时**如实告知开发者**，是否 `rebase` 由开发者决定（AI 不自动变基，同 2.3）
- 收尾由开发者完成：合并分支回主干 → `git worktree remove .worktree/{business}/{repo}` → 删除已合并分支（AI 不删分支，见 2.6；开发者明确要求时 AI 可代执行 `git worktree remove`）
- 迁移既有未提交改动进 / 出 worktree：`git diff -- <file> > x.patch` + `git -C <tree> apply x.patch`，**不要整仓 stash**——stash 会把他人改动一起带走
