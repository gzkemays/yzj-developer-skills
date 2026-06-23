---
name: project-onboarding
description: >
  将本 framework 的研发流程与前后端规范 skill 引入或融入目标项目。当用户说"引入这套规范/skills"、
  "新项目接入框架"、"把框架/skills 同步到 XX 项目"、"初始化项目 skill/规范"、"旧项目融入这套流程"、
  "adopt framework skills" 时触发。区分新项目（全量初始化）与既有项目（按基线对比合并、保留项目专有沉淀），
  产出 CLAUDE.md + .claude/skills + .document 三件套，让 AI 一进项目即可识别这套规范。
---

# 项目引入 / 融入向导（project-onboarding）

> framework 的"安装器"：把通用流程 skill、前后端规范 skill、文档骨架装进目标项目，并生成让 AI 进项目即识别规范的 CLAUDE.md。
> 本 skill 把"既有项目融入"的合并方法固化下来，避免无脑覆盖丢失项目沉淀。

## 运行前提

- 会话能同时访问 **framework 仓库**（规范源，即本仓库）与 **目标项目根目录**。
- 用户给出目标项目路径；未给则先问。

## 第〇步 · 判定场景

- 目标无 `.claude/skills/` 且无 `.document/plan/` → **A 新项目**（全量初始化）
- 已有其一 → **B 既有项目**（对比融入，外科手术式处理）

## 第一步 · 识别项目结构（两种场景都做）

- 找后端仓库（`pom.xml`/`build.gradle` + `domain/integration/interfaces/support`）、前端仓库（`package.json` + `src/views`）；判定 mono-repo 还是分仓，记录各自相对路径
- 提取占位符素材：构建命令（pom modules / package.json scripts）、设计系统 token 前缀（前端 `variables.*` / theme 文件）、契约约定（CommonResult / 分页 / 多租户 Header 等）

---

## A · 新项目全量初始化

1. **拷贝 skill**（按 cwd 分层放置）：
   - `.claude/skills/*` → `{root}/.claude/skills/`
   - `backend/*` → `{backend-repo}/.claude/skills/`
   - `frontend/*` → `{frontend-repo}/.claude/skills/`
2. **实例化 CLAUDE.md**：以 `templates/CLAUDE.md.template` 为骨架，用第一步发现填占位符；**推断不出的列出来问用户，不臆造**。
3. **文档骨架**：拷 `templates/.document/*`（`plan/STATUS.md`、`design/`、`adr/`、`developer/memory`+`capability`）。
4. **校验**：列落地清单；说"今天做什么"应触发 `iteration-planner` 读 STATUS.md（识别成功的信号）。

---

## B · 既有项目对比融入（外科手术式）

> **原则：以 framework 为基线，项目副本只增不删。** 项目专有沉淀（漏检史、项目注解、设计 token、命名规则、项目级 skill）必须保留。

1. **先备份**：目标根若非 git，先把现有 `.claude/skills`（root + 各子仓库）整体复制到 `{root}/.bak-skills-{date}/`；记录各子仓库是否 git（git 的可经其回滚）。
2. **清点**：`find` 出所有现有 skill 副本（root + 子仓库各级）、`.document/`、各级 CLAUDE.md。
3. **逐 skill 对比基线**（`diff --strip-trailing-cr 现有副本 framework当前版`，忽略行尾差异）：

   | 类别 | 处理 |
   |------|------|
   | 流程 skill（dev-session / pre-dev-alignment / progress-tracker / iteration-planner / yzj-dev-workflow / dev-output / team-memory / capability-registry / similar-issue-sweep / api-contract-checker） | 落后基线且无项目专有内容 → **framework 当前版直接覆盖** |
   | **reviewer（前 / 后端）** | **合并不覆盖**（见下「reviewer 合并标准动作」） |
   | 各域规范 skill（backend / frontend 各 skill） | 同流程 skill；留意项目对示例 / 关键词的本地增补，按"只增不删"保留 |
   | 项目专有 skill（项目独有业务约定，如 `auth-conventions` / `notification-conventions`） | **不动** |
4. **补骨架**：缺 `.document/design/` → 建 + 拷 `templates/.document/design/README.md`；缺 `.document/plan/STATUS.md` → 建。
5. **对齐 CLAUDE.md**：更新「Project Structure」（补 `design/` + STATUS.md）与「Session Workflow」（12 阶段 + 4 全程规则 + ARCH/NORMAL 分级 + P3 编码前文档分层），**保留项目专有段**（契约、多租户、权限、设计系统）。
6. **修常见问题**：
   - skill `name` 与目录名不一致（如 `name: code-reviewer` 而目录是 `reviewer`）→ 改 `name` 对齐目录
   - 路由：CLAUDE.md 声明在 root 触发的 skill（如 P1 `iteration-planner`、P9 `progress-tracker`）必须在 `{root}/.claude/skills/` 有副本
7. **校验**：每个被处理副本 `diff` 基线，结果应为"完全一致"或"基线 + 已知项目专有项"，确认无意外丢失。

### reviewer 合并标准动作（B-3 细化）

1. `cp` framework reviewer → 项目 reviewer（取得七步硬流程 + 漏检史 + 完整禁止清单 + 报告格式）。
2. **回注项目专有项**（取自备份的旧版 / 项目实际）：项目鉴权注解（如 `@RequireProjectMember`）、多租户豁免注解、设计 token（如 `var(--{prefix}-*)`）、域命名规则、项目已积累的漏检史条目。
3. `diff` 验证：与 framework 的差异应"**仅为回注的项目专有项**"。

---

## 让 AI "识别"这套规范的三件套

| 产物 | 作用 |
|------|------|
| **CLAUDE.md**（项目根 + 各子仓库） | Claude Code 按 cwd 自动加载，AI 进项目的第一识别点 |
| **.claude/skills/** | 技能随 cwd 加载：流程在 root，前后端规范在各子仓库 |
| **.document/** | 台账 / 计划 / 设计 / 沉淀，dev-session 各阶段引用 |

> 三者齐备后，新会话只要"今天做什么 / 开发 XX"即可触发 `iteration-planner` → `dev-session` 全流程。

## 反哺回路

项目开发中产生的跨项目通用能力，按 `capability-registry` 标「待反哺 framework」，迭代间歇通用化后提交回本仓库——下个项目引入即受益。
