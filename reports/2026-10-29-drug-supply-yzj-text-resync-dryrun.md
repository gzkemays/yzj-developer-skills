# 2026-10-29 re-sync dry-run：Drug Supply / yzj-text

> 基线：framework `2026-10-29`（HEAD `67881e2`）；两项目上次同步基线 `2026-10-25`（`a5bf911`）。
> 本报告为只读预演产物，目标项目未写入任何文件。合并结果暂存于会话 scratchpad，确认后才落盘。

## 1. 结构与宿主识别

| 项目 | 场景 | 宿主 | 安装模式 | root / 后端 / 前端 | 根是否 git |
|------|------|------|----------|-------------------|-----------|
| Drug Supply | B 既有 | Claude Code | 复制安装（全部层有 📌 / ℹ 项目内容，不适合改插件） | `.` / `drug-supply-datacenter-server`（YZJ 栈；erp-service、mall-service 为异框架，仅装 git-commit 等） / `drug-supply-erp-admin`（仅 i18n-automation + 项目专有技能） | 否（子仓各自 git） |
| yzj-text | B 既有 | Claude Code | 复制安装 | `.`（单仓 Rust + Tauri + SolidJS，异栈只取流程层） | 是 |

## 2. 接入后的加载顺序（不变）

Claude Code 按 cwd：根 `CLAUDE.md` + 根 `.claude/rules/` + 根 `.claude/skills/`（流程层）→ 子仓 `CLAUDE.md` + 子仓 `.claude/skills/`（Drug Supply 的 datacenter / erp-admin 等）。

## 3. 基线对比与漂移判读

10-25 → 10-29 framework 变化：新增 `neat-freak`；dev-session P12 扩为「成果报告 + 知识收尾」；流程技能中性化宿主表述（`CLAUDE.md` → 入口文件、Plan 模式 → 计划评审）；技能源目录 `.claude/skills` → `common/skills`；`templates/common/rules/collaboration.md` 新增「执行自证」「工具与真实能力」两节。

**Drug Supply**：所有副本与「10-25 基线 + `.docs` 本地化」比对后，差异全部是已登记的 📌 覆写或 ℹ 项目沉淀，**无私改漂移**：

- 📌 10 个根流程技能 + erp-admin `pre-dev-alignment`：按文件头差异清单，三方合并（旧基线 → 项目副本 → 新基线）后保留全部 📌 段；dev-session 两处、project-onboarding 一处冲突已手工解决（取新基线措辞 + 保留 📌 段），复核 diff 仅剩 📌 内容。
- ℹ datacenter `project-structure`（db/migration 说明）、`reviewer`（Operate 不继承 CommonOperate 例外）、erp-admin `i18n-automation`（PROACTIVE RULE）：同法合并保留。
- ℹ `api-contract-checker` / `skill-creator` / `yzj-dev-workflow` / datacenter `common`、`db-migration`、`model-conventions`、`testing`：仅落后基线，无项目内容。
- 5 个子仓 `git-commit` 与根副本逐字相同，同步为根合并结果。

**yzj-text**：8 个 Δ + 3 个 ℹ 抽样全量 diff 确认**均为基线更新滞后**（项目侧无任何专有行），直接覆盖即可。

## 4. 动作清单

### Drug Supply

| 动作 | 范围 | 依据 |
|------|------|------|
| 备份 | 根 + 各子仓 `.claude/skills` → `.bak-skills-2026-10-29/` | 根非 git（B-1） |
| 合并回注覆盖 | 根 `.claude/skills/` 下 10 个 📌 流程技能；文件头基线日期改 `2026-10-29`、来源路径改 `common/skills/…` | 📌 约定 |
| 直接覆盖 | 根 `api-contract-checker`、`similar-issue-sweep`、`skill-creator`；datacenter 18 个 backend 技能中无项目内容者 | 落后基线 |
| 合并保留 ℹ | datacenter `project-structure`、`reviewer`；erp-admin `i18n-automation`、`pre-dev-alignment` | 只增不删 |
| 覆盖 | 5 个子仓 `git-commit` ← 根合并结果 | 与根逐字一致 |
| 新增 | 根 `.claude/skills/neat-freak/`（不含 `.document` 引用，原样安装） | P12 依赖 |
| 合并 | 根 `.claude/rules/collaboration.md` 补新两节与中性化表述，`.document/` → `.docs/` | 模板更新 |
| 入口 | 根 `CLAUDE.md`：P12 行加 neat-freak 收尾；技能套件列表加 `neat-freak`；基线 `2026-10-25` → `2026-10-29`（3 处） | B-5 |
| 不动 | `yapd-workitem`、erp-admin / erp-service / warehouse 项目专有技能、`.bak-skills-*`、`.worktree/`、`__pycache__` | 项目专有 |

### yzj-text

| 动作 | 范围 | 依据 |
|------|------|------|
| 备份 | 依赖 git（根是 git 仓，`.claude/skills` 已入库） | B-1 |
| 直接覆盖 | `.claude/skills/` 下 13 个技能 | 纯基线滞后 |
| 新增 | `.claude/skills/neat-freak/` | P12 依赖 |
| 覆盖 | `.claude/rules/collaboration.md` ← 模板（去掉「模板来源」行） | 无项目改动 |
| 入口 | `CLAUDE.md`：基线日期、`引自 framework/skills/.claude` → `common/skills`、P12 行 | B-5 |

## 5. 风险与需开发者拍板项

1. **Drug Supply erp-admin 缺 reviewer（✗）**：本次新增的校验规则报出——装了 frontend `i18n-automation` 但无 `reviewer`。根 CLAUDE.md 记录 framework frontend 规范假设 Vue3 + Naive UI，需按模块实际栈补。默认**本次不处理**（与升级无关），仅报告。
2. **project-database-warehouse `sql-version-merge-workspace` 无 SKILL.md（?）**：项目专有目录，默认不动。
3. yzj-text 为异栈却装有 `yzj-dev-workflow` / `api-contract-checker`：沿用上次接入决定，只更新不删。
4. Drug Supply dev-session 📌 段内有本机绝对路径（vibe-pm、Design 仓位置），属既有项目覆写内容，本次不改。
5. 不 commit / push：yzj-text 改动留在工作区；Drug Supply 根内容按其约定由开发者走 vibe-pm 同步。
