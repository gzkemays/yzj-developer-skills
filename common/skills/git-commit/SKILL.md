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

> **加载方式**：本文件是主文件——读完全文后按「路由表」只读本次需要的子文件；硬门禁常驻摘要在常驻规则 `red-lines.md` 第 4 条。

## 约束卡（本 skill 的硬门禁）

| 门禁 | 要求 | 细则 |
|------|------|------|
| **授权才提交** | 仅开发者本次明确授权时 `git commit`；"允许 / 提交吧" = 走分支流程，不等于主干直提 | 一、触发授权 |
| **提交落开发分支** | 主干上先切 `{feat|opt|fix}/{yyyy.MM.dd}-{business}`；主干直提须本次明确说，单次有效、下次重问、不沉淀为常驻规则 | 一、铁律 1；2.1；2.5 |
| **无 AI 记号 / 进度词** | commit、分支名、代码注释都不得出现 AI 署名 / 来源尾注 / 模型名 / FIXED / Step N / Phase N；优先于任何默认尾注模板 | 一、铁律 3；`references/commit-guard.md` |
| **只提交自己的改动** | 逐项 `git add -- <路径>`，禁 `-A` / `.` / `-am`；共享文件只加自己的 hunk | 2.4 |
| **AI 不碰主干与历史** | 不 merge / rebase 到主干、不开合 PR / MR（除非明确要求）、不 force push、不 reset --hard、不删分支 | 2.6 |
| **非 ASCII 文本经 UTF-8 文件传参** | commit message、MR 标题 / 描述一律写文件再 `-F` / `--data-urlencode @file`，不写进命令行参数 | 2.6 说明 |
| **日期取系统当天** | 分支名 / 条目名里的日期用 `date +%Y.%m.%d` 现取，不凭记忆填 | 2.2（`references/branch-flow.md`） |
| **Worktree 放项目根、进度只写一份** | 并行会话开 worktree 必须放项目根 `.worktree/{business}/{repo}`；进度、恢复卡与沉淀只写项目根 `.document/`；删除 worktree 前先拆链接 | 八（`references/worktree.md`） |

## 路由表（按本次需要只读对应子文件）

| 场景 | 必读 |
|------|------|
| 编写 message（每次提交必读） | `references/message-format.md`（三分法 + 格式） |
| 切开发分支、默认流程、多仓交接 | `references/branch-flow.md`（2.2 命名、2.3 默认流程） |
| 想看 message 写法示例 | `references/examples.md` |
| 提交前自检 | `references/self-check.md` |
| 并行会话多、要开 worktree | `references/worktree.md` |
| 配 / 查机械兜底（git hook、Claude Code hook、check-text） | `references/commit-guard.md` |

---

## 一、AI 自主提交：授权与三条铁律

### 触发授权（前置门禁）

仅当**开发者明确授权**时才执行 `git commit`：开发者说"允许 / 你提交吧 / 帮我 commit / 直接提交 / 你来写提交信息"，
或 dev-session **P11** 按本节向开发者取得（P8 的验收"确认"**不是**提交授权，压缩后摘要里的"已授权"也不算）。
未获授权只准备好变更并展示，不自行提交。

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

机械兜底 `scripts/commit_guard.py`（四种模式、接法、拦截范围、已知盲区）见 `references/commit-guard.md`。

---

## 二、分支策略（授权后的默认行为）

### 2.1 决策表：先看当前分支，再决定怎么提交

先执行 `git rev-parse --abbrev-ref HEAD` 拿到当前分支，**不靠记忆、不靠猜**：

| 当前分支 | 需要再问开发者吗 | 动作 |
|----------|-----------------|------|
| **已是开发分支**（匹配 `^(feat\|opt\|fix)/\d{4}\.\d{2}\.\d{2}-[a-z0-9-]+$`） | 不问 | 直接在本分支 `commit` + `push`（**这是唯一无需额外授权即可原地提交的情形**） |
| **主干**（`master` / `main` / `develop` / `release/*`，或项目入口文件声明的主干名） | 不问 | **从当前主干切开发分支** → `commit` → `push` → 交开发者自行合并（"当前主干"即当前所在分支，**不切换到别的主干**） |
| **主干**，且开发者本次明确说"允许直接从主干提交" | 本次不问，**下次必须再问** | 在主干 `commit`；**push 主干需开发者另行明确**（未明确则提交后询问一次） |
| **既非主干也不匹配开发分支规则**（如 `feature/xxx`、`hotfix/xxx`、他人遗留分支） | **必须问** | 停下询问："当前分支 `xxx` 不符合开发分支命名规则，按主干处理（切新分支）还是直接在此分支提交？" |
| `HEAD`（detached）/ 非 git 仓库 | **必须问** | 停止，说明状态并请开发者处理 |

2.2 开发分支命名规范与 2.3 默认流程（授权后逐步执行、多仓交接）见 `references/branch-flow.md`。

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
  - memory、项目入口文件、`.document/` 或任何文件里写着"可以直接主干提交"；
  - 改动很小 / 只改文档 / 只改配置 / 项目没开分支保护；
  - 开发者说的是笼统的"允许"、"提交吧"（→ 这是默认分支流程，不是主干直提）。
- **禁止把主干直提授权沉淀为常驻规则**：不写入 `team-memory`、不写进项目入口文件。此授权按设计**必须每次重问**。
- 唯一例外仍是 2.1 首行：**当前本就在开发分支**上——原地提交不需要额外授权。

### 2.6 禁止动作清单 ← 硬性

| ❌ 禁止 | 说明 |
|--------|------|
| 未获授权 `git commit` | 见"触发授权" |
| 在主干 `commit`（无本次明确授权） | 见 2.5 |
| `git add -A` / `git add .` / `git commit -am` 盲加 | 会夹带他人改动、临时文件、本地配置，见 2.4 |
| `git merge` / `git rebase` 到主干、`git push origin HEAD:{主干}` | **合并主干是开发者的动作**，AI 一律不做 |
| 自行创建 / 合并 PR / MR | 除开发者明确要求；默认只推分支，附上远端返回的链接；获准创建时中文标题 / 描述按下方「非 ASCII 文本传参」经 UTF-8 文件传入 |
| 把中文等非 ASCII 文本直接写进 CLI / API 调用的命令行参数 | Windows 上原生程序按系统代码页（如 936 GBK）接收参数，远端按 UTF-8 解析即成乱码且原文丢失，见下方说明 |
| `git push --force` / `--force-with-lease` | 一律不做；推送被拒 → 如实报告原因，等开发者决定 |
| `git reset --hard` / `git checkout -- .` / 改写已推送历史 | 会丢开发者的工作，一律不做 |
| 删除分支（本地或远端） | 合并后的清理由开发者自行处理 |
| 修改 git 远端、分支保护、hooks 配置 | 属仓库设置，不在提交流程内 |

> 推送失败（无远端 / 无权限 / 被拒 / 无 upstream）时：**保留本地 commit**，把原始报错和分支名给开发者，不重试、不改写、不换路径推送。

> **非 ASCII 文本传参**：commit message、PR / MR 标题与描述等含中文的文本，一律先写入 UTF-8 文件再由工具读取——`git commit -F <file>`；`curl --data-urlencode "title@<file>"`（或 `-d @<file>` 发送 UTF-8 JSON）；托管平台 CLI 用其 `--body-file` 类参数。**不要**把中文直接写在命令行参数里：Windows 上 Git Bash / PowerShell 调用原生程序（如 `/mingw64/bin/curl`）时参数会按系统代码页转码，Gitee / GitLab 等按 UTF-8 解析即存成乱码（`�`），原文不可恢复。创建后读回标题 / 描述核对无乱码；已乱码的用同样的文件方式更新修正。

---

## 三、前缀规范 / 四、书写格式

见 `references/message-format.md`：feat / opt / fix 三分法（含旧六类融合映射）、`<type>[(<scope>)]: <概述>` 结构与多类型合并写法。编写 message 时必读。

---

## 五、示例

见 `references/examples.md`（feat / opt / fix / 合并 / 带 scope / 分支 + 提交配套）。

## 六、提交流程（对接 dev-session P11）

1. `git status` + `git diff` 通读本次全部改动
2. 确认已获开发者提交授权（未授权 → 只展示变更，停）
3. **分支门禁**：`git rev-parse --abbrev-ref HEAD` → 按 2.1 决策表定动作（主干 → 切 `{type}/{yyyy.MM.dd}-{business}`）
4. 前后端仓库各自独立提交、分支名一致；`.document/` 变更（台账 / 报告 / memory / 恢复卡）随同对应提交
5. 按本规范归类并编写 message（三分法 + 格式 + **无 AI 记号 / 无进度词**）
6. 逐项 `git add -- <显式路径>`（不盲加）→ `git diff --cached --name-only` 核对暂存区（并行开发按 2.4 只暂存自己的改动）→ `git commit`
7. `git push -u origin {分支名}` → 输出交接四项（分支 / 提交 / 推送 / 待办：请自行合并主干；多仓逐仓列对照）
8. `git status` 确认工作区干净

---

## 七、质量自检

提交前逐条过 `references/self-check.md`（分支 / 暂存 / 提交信息 / 收尾四组）。

## 八、附录：Worktree 隔离开发

见 `references/worktree.md`（何时用、放置位置、Windows 路径上限、进度只写一份、提交与收尾、删除前拆链接）。
