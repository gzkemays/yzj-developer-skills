# YAPD 接入 dry-run 报告（common 新基线）

验证日期：2026-10-28
基线：framework/skills 分支 `feat/2026.10.28-skill-loading-adapter-2`（common 化 + Codex 报告三问题修复，修复批未提交）
目标项目：`D:/.project/yapd`（**全程只读，未写入任何文件**）
性质：模拟 `project-onboarding` B（既有项目对比融入）的识别 → 对比 → 动作推演；不是实际接入。

## 一、结构与宿主识别

| 角色 | 识别结果 | 标志 |
|------|---------|------|
| 项目根 | `yapd/`（非 git 仓） | `.document/` |
| 后端仓 | `yadp-server/`（嵌套 Maven：yapd-server + yapd-common） | pom.xml |
| 前端仓 | `yadp-web/` | Vue + src/views |
| 宿主 | **多宿主**：`.claude/`（三层）+ `.agents/`（三层，2026-10-28 Codex 适配层产物）并存 | — |

排除项（不计入对比）：`.scratch/feishu-web-master-*`（临时参考副本）、`yadp-server/.claude/worktrees/*`（宿主托管 worktree 副本）——本次 dry-run 发现 verify-baseline 原本会把这两类计入，已在脚本中加排除。

## 二、接入后的预期加载顺序

**Claude Code 侧**（宿主自动加载，按 cwd）：
- root 会话：根 CLAUDE.md + 根 `.claude/rules/`（**当前缺失，接入时补**）+ 根 `.claude/skills/`（流程层）
- yadp-server 会话：根链 + 后端 CLAUDE.md + 后端 `.claude/skills/`
- yadp-web 会话：根链 + 前端 CLAUDE.md + 前端 `.claude/skills/`

**其他宿主侧**（显式加载，按入口声明）：
- 各层 AGENTS.md（新模板重实例化）→ 先读 `common/rules/collaboration.md`（契约任务加读 api-contract.md）→ 按路由读 `common/skills/<name>/SKILL.md` 全文 → 执行门禁五条约束全程生效
- `.agents/` 旧适配层整体移除，由与 `.claude/skills` 同源的 `common/skills/` 副本取代

## 三、基线对比结果（排除修复后）

```
✓ 一致 4   ℹ 项目专有差异 20   📌 项目覆写 0   Δ 流程漂移 15   ✗ 结构错误 0   （默认模式退出码 0）
ℹ 项目根无常驻规则层（.claude/rules 或 common/rules）
```

漂移构成已抽样证实为两类，无项目覆写标记（📌 = 0）：
1. **新基线中性化**：如 root `capability-registry` 差 2 行 = 恰好是 `skills/.claude/skills`→`common/skills` 的路径更新；`team-memory` 差 13 行 = 个人 memory 宿主映射 + 入口文件化表述。
2. **副本滞后**：root `git-commit` 差 115 行、子仓差 261 行（分支门禁 / Worktree 附录等多轮基线更新未同步）；`progress-tracker` 根 84 / 子仓 141 行；root 副本比子仓副本新，说明历史上只同步过根层。

## 四、真实接入（B 流程）将执行的动作

| # | 动作 | 范围 | 依据 |
|---|------|------|------|
| 1 | 流程 skill 直接覆盖为新基线 | 15 个 Δ（root 9 + server 3 + web 3：dev-session / pre-dev-alignment / progress-tracker / iteration-planner / git-commit / team-memory / capability-registry / dev-output） | 无 📌 覆写标记，落后基线且未见项目专有硬约束 |
| 2 | 规范 skill 合并不覆盖 | 20 个 ℹ（两端 reviewer、database-design 272 行、mybatis 270 行、db-migration 79 行等） | 项目沉淀（漏检史 / 项目注解 / 本地规则）须保留回注；db-migration 为项目改造版（YAPD 用自有迁移策略），覆盖前按「📌 项目覆写约定」把项目差异标记回文件头 |
| 3 | 项目专有 skill 不动 | ui-ux-pro-max、yapd-workitem、auth-conventions、notification-conventions | ⊘ framework 无 |
| 4 | 补常驻规则层 | `templates/common/rules/*` → 根 `.claude/rules/`（Claude）+ 根 `common/rules/`（其他宿主） | 根当前无 rules |
| 5 | 根 CLAUDE.md 对齐 | 补 framework 基线注记（现为 2026-07-19 旧版、无基线行）；Session Workflow 对齐 12 阶段新表述；多宿主首行 `@AGENTS.md` | CLAUDE.md.template |
| 6 | `.agents/` 层移除 + AGENTS.md 重实例化 | 三层 `.agents/skills`、`.agents/rules` 删除；三份 AGENTS.md 用新模板重写 | 旧层来源 `4566de4`（已废弃的生成式适配）；现三份 AGENTS.md 均以**绝对路径**做加载引用（`D:/.project/yapd/.document`、`D:/.project/yapd/yadp-server/.agents/skills`、布局表全行），违反约定 A；重写时项目专有内容（YZJ 命令、yapd-* 技能路由、授权约束）保留迁入 |
| 7 | 弃用项清理 | server 的 `framework-usage`（✓ 一致但基线已标弃用） | 移除或保留为转向说明，由开发者定 |
| 8 | 校验 | `verify-baseline.sh D:/.project/yapd --show-diff`：流程 skill 应全 ✓，ℹ 仅剩项目专有差异；入口无绝对路径检查 | 引入后验证清单 |

**注意**：动作 1 覆盖前仍需逐个确认 15 个漂移副本中无未标记的项目专有改动（本次只抽样了 4 个小漂移 + 确认 0 📌；git-commit / progress-tracker 的大漂移在真实接入时应 `--show-diff` 全量过目）。

## 五、本次 dry-run 顺带修复的工具问题

- `verify-baseline.sh` 新增排除：`*/.claude/worktrees/*`（宿主托管 worktree）、`*/.scratch/*`（临时参考副本）——修复前 YAPD 被多计 2 个技能目录（34 项噪音：✓8/ℹ35/Δ22 → 修复后 ✓4/ℹ20/Δ15）。

## 六、未验证项

- 本报告是文件层推演：未实际执行接入，未在 YAPD 启动新会话验证触发路由（接入后需按「引入后验证」C 组做行为验证）。
- 其他宿主对新 AGENTS.md 的实际加载（需接入后用 Codex 等冷启动实测）。
