---
name: project-onboarding
description: >
  将本 framework 的研发流程与前后端规范 skill 引入或融入目标项目。当用户说"引入这套规范/skills"、
  "新项目接入框架"、"把框架/skills 同步到 XX 项目"、"初始化项目 skill/规范"、"旧项目融入这套流程"、
  "adopt framework skills" 时触发。区分新项目（全量初始化）与既有项目（按基线对比合并、保留项目专有沉淀、
  流程 skill 的项目专有硬约束按「📌 项目覆写约定」回注），并按宿主产出入口四件套——Claude Code：
  CLAUDE.md + .claude/rules + .claude/skills + .document；其他模型宿主：AGENTS.md + common/skills +
  rules 引用 + .document——让任意 AI 宿主一进项目即可识别这套规范，无需逐宿主定制。
---

# 项目引入 / 融入向导（project-onboarding）

> framework 的"安装器"：把通用流程 skill、前后端规范 skill、文档骨架装进目标项目，并生成让 AI 进项目即识别规范的宿主入口。
> 本 skill 把"既有项目融入"的合并方法固化下来，避免无脑覆盖丢失项目沉淀。

## 运行前提

- 会话能同时访问 **framework 仓库**（规范源，标志：`common/skills/` + `templates/AGENTS.md.template`）与 **目标项目根目录**。
- 用户给出目标项目路径；未给则先问。安装后的技能副本不一定在源库旁边——re-sync 时以目标入口文件记录的「来源注记」与用户给出的源库位置为准，不从技能副本的位置反猜源库。

## 两条硬约定（所有写入目标项目的内容必须遵守）

1. **相对路径**：写入目标项目的入口文件（CLAUDE.md / AGENTS.md）与规则中，对技能、规则、`.document/` 的**加载引用一律用相对路径**（以入口文件所在目录为基准）；**禁止绝对路径**——同一父目录常并存多个项目，且项目会被迁移 / 改名，绝对路径迁移即失效。指向 framework 源库的信息（来源、基线版本）只作**来源注记**，不作为加载路径。验收口径：**整个项目目录移动 / 改名后，所有引用无需修改仍然成立**。
2. **执行门禁不得删减**：用 `templates/AGENTS.md.template` 实例化时，「执行门禁」一节**原样保留**（删除不适用的技能路由可以，门禁条款不可以）——它是防止接入宿主"只看 description 不读全文、跳过审查、虚报验证"的兜底。

## 第〇步 · 判定场景与宿主

- 目标无技能目录（`.claude/skills/` 与 `common/skills/` 均无）且无 `.document/plan/` → **A 新项目**（全量初始化）
- 已有其一 → **B 既有项目**（对比融入，外科手术式处理）
- **宿主判定**：问清或从上下文确认团队使用的 AI 宿主——**Claude Code** / **其他模型宿主** / **多宿主并用**。拿不准 → 问用户，不臆测。

## 第一步 · 识别项目结构（两种场景都做，**不要假设仓库叫什么名字**）

**按标志文件识别，而非按目录名**——不同项目布局不同（分仓 / mono-repo / 单栈 / 嵌套 Maven 都要支持）：

| 角色 | 识别标志（命中任一） |
|------|----------------------|
| **后端仓库** | 目录内直接有 `pom.xml` / `build.gradle*`；或同时有 `domain/`+`integration/`；或 `src/main/java` |
| **前端仓库** | `package.json` 依赖含 `vue`；或有 `src/views/` |
| **项目根** | 含 `.document/`，或前后端仓库的共同父目录 |

- 用 `Glob`/`Grep` 扫描目标项目定位上述标志，得出 **{root} / {backend-repo} / {frontend-repo} 的实际相对路径**（可能分仓、mono-repo `apps/api`+`apps/web`、或单栈）。
- **命中多个 / 零个 / 拿不准 → 列候选问用户**，不臆测、不照搬别项目（如 YAPD 的 `yadp-server`/`yadp-web`）的命名。
- 把识别结果写进项目根入口文件的「Project Structure」与「Working Directory Routing」，作为该项目布局的权威记录（后续 re-sync / 校验据此）；路径一律写相对 {root} 的形式。
- 提取占位符素材：构建命令（pom modules / package.json scripts）、设计系统 token 前缀（前端 `variables.*` / theme 文件）、契约约定（CommonResult / 分页 / 多租户 Header 等）。

> 这套标志被 `scripts/verify-baseline.sh` 复用（自动判定每个技能目录属于前/后/根，再对应 framework 比对）——识别逻辑两边一致。

---

## A · 新项目全量初始化

### A-1 Claude Code 项目（四件套）

1. **拷贝 skill 与常驻规则**（按 cwd 分层放置）：
   - `templates/common/rules/*` → `{root}/.claude/rules/`（协作原则 + 契约速查；Claude Code 自动加载，契约占位符按项目填）
   - `common/skills/*` → `{root}/.claude/skills/`
   - `backend/*` → `{backend-repo}/.claude/skills/`
   - `frontend/*` → `{frontend-repo}/.claude/skills/`
2. **实例化 CLAUDE.md**：以 `templates/CLAUDE.md.template` 为骨架，用第一步发现填占位符；**推断不出的列出来问用户，不臆造**。契约速查表只填在 `rules/api-contract.md`，CLAUDE.md 不重复。
3. **文档骨架**：拷 `templates/.document/*`（`plan/STATUS.md`、`design/`、`adr/`、`developer/memory`+`capability`）。
4. **校验**：列落地清单；跑 `bash scripts/verify-baseline.sh {项目根}` 过结构 + 基线（见 README「引入后验证」）；说"今天做什么"应触发 `iteration-planner` 读 STATUS.md（识别成功的信号）。

### A-2 其他模型宿主项目（AGENTS.md 入口）

1. **拷贝技能与规则**（内容与 Claude 侧完全同源，无需任何适配）：
   - `common/skills/*` → `{root}/common/skills/`
   - `templates/common/rules/*` → `{root}/common/rules/`（契约占位符按项目填）
   - `backend/*` → `{backend-repo}/common/skills/`、`frontend/*` → `{frontend-repo}/common/skills/`（单仓 / mono-repo 可统一放根 `common/skills/`，但同栈才装）
2. **实例化 AGENTS.md**：以 `templates/AGENTS.md.template` 为骨架——技能位置、规则引用全部写相对路径；「执行门禁」节原样保留；「技能来源」填 framework 来源注记（仅记录，不作加载路径）。会被单独打开的子仓各放一份 AGENTS.md（引用各自根内的技能目录）。
3. **文档骨架**：同 A-1 第 3 步。
4. **校验**：跑 `bash scripts/verify-baseline.sh {项目根}`（已兼容 `common/skills` 布局）；从目标项目启动该宿主新会话，验证入口可读、典型请求能路由到对应 SKILL.md 并**读全文执行**。只做了文件校验时如实说明"自动触发未实测"。

### A-3 多宿主项目

- 执行 A-2（`common/` 为唯一内容源 + AGENTS.md），再执行 A-1 的第 1、2 步把 `common` 内容**复制**到各级 `.claude/`（Claude Code 只认 `.claude/skills` / `.claude/rules`，这是宿主硬约束）；CLAUDE.md 首行 `@AGENTS.md` 导入通用入口，其后只写 Claude 专属补充。
- 两份副本内容同源；re-sync 时两处一起更新，`verify-baseline.sh` 对两处都校验。

---

## B · 既有项目对比融入（外科手术式）

> **原则：以 framework 为基线，项目副本只增不删。** 项目专有沉淀（漏检史、项目注解、设计 token、命名规则、项目级 skill）必须保留。**不移动、不删除其他宿主的既有目录。**

1. **先备份**：目标根若非 git，先把现有技能目录（root + 各子仓库，含 `.claude/skills` 与 `common/skills`）整体复制到 `{root}/.bak-skills-{date}/`；记录各子仓库是否 git（git 的可经其回滚）。
2. **清点**：`find` 出所有现有 skill 副本（root + 子仓库各级、两种布局）、`.document/`、各级入口文件（CLAUDE.md / AGENTS.md）。
3. **逐 skill 对比基线**（`diff --strip-trailing-cr 现有副本 framework当前版`，忽略行尾差异）：

   | 类别 | 处理 |
   |------|------|
   | 流程 skill（dev-session / pre-dev-alignment / progress-tracker / iteration-planner / yzj-dev-workflow / dev-output / team-memory / capability-registry / similar-issue-sweep / api-contract-checker / git-commit） | 落后基线且无项目专有内容 → **framework 当前版直接覆盖**；含项目专有硬约束 → 按下「📌 项目覆写约定」回注后覆盖 |
   | **reviewer（前 / 后端）** | **合并不覆盖**（见下「reviewer 合并标准动作」） |
   | 各域规范 skill（backend / frontend 各 skill） | 同流程 skill；留意项目对示例 / 关键词的本地增补，按"只增不删"保留 |
   | 项目专有 skill（项目独有业务约定，如 `auth-conventions` / `notification-conventions`） | **不动** |
4. **补骨架**：缺 `.document/design/` → 建 + 拷 `templates/.document/design/README.md`；缺 `.document/plan/STATUS.md` → 建；缺常驻规则层 → 按宿主拷 `templates/common/rules/*`（Claude Code 放 `.claude/rules/`，其他宿主放 `common/rules/` 并在 AGENTS.md 显式引用；项目入口已有契约表的，搬进 `rules/api-contract.md` 或留在原处二选一，不重复维护）。
5. **对齐入口文件**：更新「Project Structure」（补 `design/` + STATUS.md）与「Session Workflow」（12 阶段 + 4 全程规则 + ARCH/NORMAL 分级 + P3 编码前文档分层），**保留项目专有段**（契约、多租户、权限、设计系统）；AGENTS.md 的「执行门禁」节缺失则补回。检查并**替换入口中的绝对路径为相对路径**（两条硬约定）。
6. **修常见问题**：
   - skill `name` 与目录名不一致（如 `name: code-reviewer` 而目录是 `reviewer`）→ 改 `name` 对齐目录
   - 路由：入口声明在 root 触发的 skill（如 P1 `iteration-planner`、P9 `progress-tracker`）必须在 root 技能目录有副本
7. **校验**：跑 `bash scripts/verify-baseline.sh {项目根} --show-diff`——流程 skill 应"✓ 一致"，`reviewer`/规范 skill 的差异（ℹ）应仅为项目专有项，确认无意外丢失。

### reviewer 合并标准动作（B-3 细化）

1. `cp` framework reviewer → 项目 reviewer（取得七步硬流程 + 漏检史 + 完整禁止清单 + 报告格式）。
2. **回注项目专有项**（取自备份的旧版 / 项目实际）：项目鉴权注解（如 `@RequireProjectMember`）、多租户豁免注解、设计 token（如 `var(--{prefix}-*)`）、域命名规则、项目已积累的漏检史条目。
3. `diff` 验证：与 framework 的差异应"**仅为回注的项目专有项**"。

### 📌 项目覆写约定（B-3 细化：流程 skill 带项目专有硬约束时）

流程 skill 原则上与基线逐字一致；项目确有必须偏离的硬约束（如"本项目 AI 只 commit 不 push"、"monorepo 根不是 git 仓，根目录沉淀不提交"）时，**不散改正文**，按以下约定回注，让 re-sync 可机械保留：

1. **文件头差异清单**：frontmatter 之后紧跟一段引用块，逐条列出与基线的差异与依据：
   > **本文件 = framework 基线 {基线日期} + 项目专有项回注。** 差异仅限以下 N 处，均以「📌 {项目}」标记：① … ② …。其余与基线逐字一致，re-sync 时保留这 N 处。
2. **正文逐处标记**：每一处偏离的行 / 段落以 `📌 {项目}` 开头（或行内标注），说明覆写内容与依据（指向项目入口文件 / rules 的哪条）
3. **只覆写不删除**：基线原文保留（可改写为"基线：…；本项目：…"），便于对照
4. **re-sync 动作**：`cp` 基线 → 按文件头清单逐条把 📌 段回注 → `diff` 验证差异仅为 📌 行；`verify-baseline.sh` 对含 📌 的流程 skill 报「📌 项目覆写」而非「Δ 流程漂移」
5. **不得覆写的**：主干直提单次授权、P4 Review 不可跳过、P8 开发者确认之类"按设计必须每次重问 / 不可跳过"的门禁，不得以 📌 固化为常驻放宽；AGENTS.md「执行门禁」节同理不得删减放宽

---

## 让 AI "识别"这套规范的四件套（按宿主）

| 产物 | Claude Code | 其他模型宿主 |
|------|-------------|--------------|
| **入口文件** | CLAUDE.md（项目根 + 各子仓库，按 cwd 自动加载；多宿主时首行 `@AGENTS.md`） | AGENTS.md（项目根 + 会被单独打开的子仓，各自引用根内相对路径） |
| **常驻规则** | `.claude/rules/`（自动加载，可用 `paths:` 限定触发范围） | `common/rules/`（AGENTS.md 显式要求读取，不依赖自动扫描） |
| **技能目录** | `.claude/skills/`（随 cwd 加载：流程在 root，前后端规范在各子仓库） | `common/skills/`（AGENTS.md 声明位置；用前必读 SKILL.md 全文） |
| **共享文档** | `.document/`（台账 / 计划 / 设计 / 沉淀，dev-session 各阶段引用） | 同左（全项目唯一一份，位置写进 AGENTS.md） |

> 四者齐备后，新会话只要"今天做什么 / 开发 XX"即可触发 `iteration-planner` → `dev-session` 全流程。
> 不复制个人 settings、凭据、`settings.local.json` 到目标项目；接入授权不包含 commit / push——提交另按 `git-commit` 取得授权。

## 反哺回路

项目开发中产生的跨项目通用能力，按 `capability-registry` 标「待反哺 framework」，迭代间歇通用化后提交回本仓库（流程类 → `common/skills/`，后端 → `backend/`，前端 → `frontend/`）——下个项目引入即受益。
