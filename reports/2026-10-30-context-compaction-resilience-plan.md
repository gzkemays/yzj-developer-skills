# 2026-10-30 方案：小上下文模型压缩后约束不丢失（通用化 + 主文件引导式瘦身）

> 状态：方案已三轮核对定稿；批次 A、B 试点、质量检查修复、批次 C 均已合并 master（!16、!17、!18）；批次 C 合并后质检发现 2 个阻断（pretooluse 的 stdin 编码、引号内分隔符导致静默放行）与 9 项应修，已在 `fix/2026.10.30-commit-guard-hardening` 修复——整体 shlex 分词 + 解析失败退化为全文扫描、`-am` 短选项簇、`-C <commit>` 与 `-C <dir>` 区分、deny 先于 ask、`#` 行只在编辑器提交时忽略、模型名排除仅限路径 / 文件名语境、hook 查找仓库内优先、主干名 `yzj.trunk` 配置接入、文档口径改为"对已启用 hooksPath 的成员生效"、verify-baseline 增 `.githooks` 检查、hooks.json 无 python 时提示。Codex 侧待实机核实。**批次 B 其余已合并**（!20）：pre-dev-alignment 30→12.7KB（4 references + 3 templates）、git-commit 26→13.6KB（6 references）、yzj-dev-workflow 24→13.7KB（3 references，删第 6 节）、前后端 reviewer 只重排（七步 → 漏检史 → 禁止清单 → 报告格式 → 维度），章节编号不变。合并后质检：`verify-baseline.sh` 原只比对 `SKILL.md`、子文件缺失 / 过期仍报一致，已改为比对整个技能目录（references / templates / scripts）；搬入子文件后 11 处"见下文 / 主文件第 N 章"指针改为经主文件路由表定位；`check-skill-layout.sh` 新增 references 互引检查（templates 与所属阶段子文件互指门禁行允许）。D 未开始。基线日期按"同日只发布一次"规则暂不提升，随下次基线一并发布。
> 合并后质量检查（独立审查 + 机械检查）：无阻断；8 项 should-fix + 9 项 nit 已在 `fix/2026.10.30-compaction-review-fixes` 修复——分支重开序号 `-2` 的定位、项目根取最近而非最远、`check-skill-layout` 引用存在性不再被目录守卫跳过、red-lines 指针逐字对齐原标题、review 报告任何级别落档且文件名统一带日期、slug = business = worktree 目录名写入规则、恢复卡搁置保留 / 取消删除。
> 试点结果：dev-session 主文件 30.9KB → 8.9KB（约束卡 / 分级 / 路由表 / 回退 / 进度判定），5 个 `references/` 子文件 1.5–6.0KB，2 个 `templates/`；单阶段加载 ≈ 主文件 + 1 子文件 ≈ 15KB。
> 适用宿主：Claude Code、Codex、以及经各类宿主接入的 DeepSeek 等模型——本方案核心机制一律放在**通用层**，宿主专属只做薄适配。
> 基线：`2026-10-30`。本方案分 A–D 四批，每批单独提交并发布一次基线。

---

## 1. 问题

在上下文窗口较小的模型上（64k / 128k），一次完整后端流程要先读进约 150–200KB 规范（4–6 万 token），压缩几乎必然发生；压缩后会话中途读入的技能正文被概括，门禁细节（"P4 不可跳过"、"修复后重走 P4–P7"、"主干直提单次授权"）退化成一句"按 dev-session 开发"，随后被跳过。

实测各大技能体积（字节）：

| 技能 | 总计 | 最大章节 |
|------|------|---------|
| `backend/reviewer` | 43,707 | 〇 七步硬流程 8.5K；十五 禁止清单 6.0K；五 注释规范 6.0K |
| `common/skills/pre-dev-alignment` | 30,199 | 文档模板 7.1K；标准执行流程 6.6K |
| `common/skills/dev-session` | 26,294 | P3 3.2K；P5 3.1K（含用例模板） |
| `common/skills/git-commit` | 26,341 | 二 分支策略 9.7K；八 Worktree 附录 6.6K |
| `common/skills/yzj-dev-workflow` | 23,720 | 0 编码前门禁 4.7K；6 完整研发流程总览 3.5K（与 dev-session 重复） |
| `common/skills/project-onboarding` | 21,148 | A 新项目 6.0K；B 既有项目 5.8K |

## 2. 已核实的事实（Claude Code 官方文档；其他宿主另标）

| 内容 | 压缩后 | 对设计的含义 |
|------|--------|-------------|
| 根 CLAUDE.md、无 `paths:` 的 `.claude/rules/*.md` | 从磁盘重新注入 | 红线放这一层最可靠 |
| 带 `paths:` 的 rules、子目录 CLAUDE.md | 仅再次触碰匹配文件时加载 | 红线不能带 `paths:` |
| 已调用技能正文 | 只重注入**开头**：单技能 ≤ 5k token，合计 ≤ 25k，**最早加载的先丢** | 约束必须在主文件开头；总入口 dev-session 最先加载、最先被丢 → 更要靠 rules + 状态文件兜底 |
| 仅对话中说过的约束 | 不保留 | 一切约束落文件 |
| `SessionStart` hook（matcher `compact`） | 压缩后重新执行，stdout 注入上下文 | 可自动重注入红线 + 当前阶段 |
| `PreToolUse` hook（Bash，`git commit *`） | 可硬拦（exit 2 / `deny`），原因回传模型；也可 `ask` 弹窗 | 不依赖模型记得规则 |
| 插件 `hooks/hooks.json` | 启用插件即生效；脚本路径用 `${CLAUDE_PLUGIN_ROOT}` | 插件安装的项目无需额外配置 |
| `PreCompact` 影响摘要内容 | **未核实**（文档只记载"可阻止压缩"） | 不依赖 |
| CLAUDE.md 写"压缩时保留 X" | **未核实** | 不依赖 |
| Codex：hook、压缩后是否重读 AGENTS.md | **未核实**（第三方资料称 0.129+ 有 PreCompact/PostCompact hook；有 issue 报告 AGENTS.md 偶发丢失） | 其他宿主只能靠：入口文件文字协议 + 状态文件 + git 原生 hook |

## 3. 设计原则

1. **约束不靠记忆**：可靠度排序 = 机械拦截 > 每次重注入的文件 > 技能主文件开头 > 对话记忆。
2. **红线单一源**：rules 自动加载和 hook 注入读同一个文件，不复制。
3. **进度以磁盘为准**：STATUS 阶段列 + 产物文件存在性；压缩后读一眼磁盘即可重新定位（参考 skill-project-master 的 `ds-next`）。
4. **授权不入状态**：提交 / 主干直提授权单次有效，写进 STATUS 反而会让压缩后的模型误以为仍有授权；STATUS 只记阶段与已过门禁。
5. **通用优先**：核心逻辑用 Python 脚本放在**技能目录内**，随技能复制 / 随插件分发；宿主适配只调用同一脚本。
6. **主文件引导、按阶段加载**：大技能拆成"主文件（约束卡 + 路由表）+ 阶段子文件"，一次只读当前阶段；门禁第 1 条措辞相应调整。

## 4. 已定决策

| # | 决策 | 结论 |
|---|------|------|
| 1 | 覆盖范围 | 通用：Codex、DeepSeek 等所有接入方式，不为 Claude Code 单独优化 |
| 2 | 红线位置 | 单独文件 `red-lines.md`（不并入 collaboration.md） |
| 3 | 脚本语言 | Python（与 `reviewer/scripts/review-scan.py` 一致，规避 Windows 下 shell 差异） |
| 4 | 主干直提 | Claude Code 用 `ask` 弹窗；其他宿主为自检提醒 + 文字门禁（git hook 分不清人与 AI，硬拦会挡住开发者自己合并主干） |
| 5 | 拆分粒度 | **主文件 + 同一技能内的子文件**（不拆成多个独立技能）：P1–P12 不会被单独触发；技能数不膨胀；安装与 verify 逻辑不变 |
| 6 | 门禁第 1 条 | 改为"读完主文件全文 + 路由表指向当前阶段的子文件"，同步改 AGENTS.md / collaboration.md / 两份入口模板 |
| 7 | git 原生 hook | 启用：`project-onboarding` 接入时设 `core.hooksPath=.githooks`；AI 记号规则对人提交也无害 |
| 8 | 红线写法 | 红线**不是规则的概括替代**：每条只写"不可违反的结论 + 指向原规则章节的指针"，恢复协议要求进入门禁前按指针重读原章节全文 |
| 9 | STATUS 列 | 拆成两列「阶段」「已过门禁」 |
| 10 | 恢复内容按需求隔离 | 每个需求一张**恢复卡** `.document/plan/context/{slug}.md`，由 agent 在 P1 建立、每次阶段迁移时更新；`restore_context.py` 按当前需求（分支名 / worktree 路径 / `--task`）只恢复自己那张，不做根目录统一恢复 |
| 11 | reviewer | **P4 全量加载，不拆分**（兜底硬门禁）；只重排章节让门禁与清单靠前，并建议有子代理能力的宿主把 P4 放到独立子代理执行 |
| 12 | yzj-dev-workflow 第 6 节 | **删除**（第二轮确认）：核对后其内容已被覆盖——流程步骤 ⊂ dev-session 12 阶段，按关注点列 backend 技能 = 本技能第 8 节「Skill 引用速查表」，4 条关键控制点 = dev-session 门禁；原位留一句指向 dev-session 与第 8 节 |
| 16 | P5 用例拟定原则 | 按实际场景拟定、有设计文档则据其验收标准展开；回归按影响面划定、不过度回归；拿不准时与开发者对齐一次再执行 |
| 13 | 体积阈值 | 只**告警不阻断**：主文件 > 8KB、子文件 > 12KB 告警；规则会随能力累积增长，阈值不做硬限制。硬失败只针对路由指向的文件不存在、孤立文件 |
| 14 | Codex 适配 | 先在 Codex 实机核实 hook 机制与 AGENTS.md 压缩后是否重读，核实后再决定适配方式；批次 C 先做 git hook + 文字协议 + Claude Code 适配 |
| 15 | 批次顺序 | A → B（dev-session 试点）→ C → B 其余 → D |

---

## 5. 批次 A · 状态外置与恢复协议（通用）

### A-1 新增 `templates/common/rules/red-lines.md`（≤ 40 行，无 `paths:`）

**定位**：红线是"结论 + 指针"，不是规则的概括替代。每条只写不可违反的结论，后面跟 `→` 指向原规则的技能与章节标题（指章节名不指行号，拆分后仍有效）；恢复协议第 4 条要求进入门禁前按指针重读原章节全文，质量由原规则保证，红线只负责"让模型记得去读"。

草案：

```markdown
# 红线（常驻，压缩后首先重读）

> 本文件是流程硬门禁的最小集合，所有宿主常驻加载。每条后的 → 是原规则位置：执行该门禁前必须重读原章节全文，本文件不替代原规则。与技能正文冲突时以本文件为准，并停下报告冲突。

## 硬门禁（任何阶段、任何改动量都不得跳过）
1. 编码后必过 P4 AI Review，"改动小 / 有把握"不是理由。→ dev-session「规则 4」「P4」；前/后端 reviewer「七步硬流程」「放行门禁」
2. P6/P7 发现问题后的修复同样是编码：修复 → P4 → P5 → P6 → P7 完整重走，禁止只复测失败用例。→ dev-session「P7」「流程控制·回退规则」
3. P8 开发者确认、P9 台账更新是硬门禁：台账未更新不得宣布"完成"。→ dev-session「P8」「P9」；progress-tracker
4. 未获本次明确授权不 commit / push；commit 与分支名不留任何 AI 记号与进度词；主干直提授权单次有效、下次重问。→ git-commit「一、授权与三条铁律」「2.5」「2.6」
5. 开发者纠正 → 立即沉淀 feedback memory；修复一处 → 全库回溯同类。→ dev-session「规则 1」「规则 2」；team-memory；similar-issue-sweep
6. 审查 / 自测结论附文件级依据；未跑过的命令不得称"已验证"。→ 入口文件「执行门禁」3、4
7. 编码前文档评审门禁（L2 技术设计 / L3 需求 + 设计）未通过不得编码。→ pre-dev-alignment「任务分级」「Review 门禁机制」

## 压缩恢复协议（发现上下文被压缩 / 看到摘要 / 想不起当前阶段门禁细节时）
1. 先运行 `restore_context.py`（无 Python 时手动）：读本需求的恢复卡 `.document/plan/context/{slug}.md` 与 STATUS 对应行，确认当前阶段、已过门禁、下一步。
2. 按恢复卡「需重读」清单重读：当前阶段技能的主文件 + 路由表指向的子文件；P4 阶段重读 reviewer 全文。
3. 输出一行定位回执 `[恢复 | 需求 … | 阶段 Px | 已过 … | 下一步 …]`，再继续。
4. 不凭记忆推进门禁：进入 P4 / P8 / P9 / P11 前，按本文件 → 指针重读原章节全文。
5. 授权不从摘要里继承：提交 / 主干直提 / 计划批准一律重新向开发者确认。
```

### A-2 入口模板写入恢复协议（不只放 rules）

- `templates/AGENTS.md.template`「开始工作时」后新增 5 行「压缩恢复」（与 red-lines 第二节同义、更短），并在「执行门禁」旁显式引用 `common/rules/red-lines.md`。
- `templates/CLAUDE.md.template`：「全程规则（不可妥协）」4 条改为指向 `.claude/rules/red-lines.md`（避免双源），Rules 表加一行 red-lines；新增同样 5 行恢复协议。
- 本仓库 `AGENTS.md`「执行门禁」第 1 条与 `templates/common/rules/collaboration.md`「执行自证」第 1 条：措辞改为"主文件全文 + 当前阶段子文件"。

### A-3 STATUS 增加「阶段」「已过门禁」两列

`templates/.document/plan/STATUS.md`「进行中」表：

```
| 需求 | 状态 | 阶段 | 已过门禁 | 负责人 | 计划文档 | 涉及模块 | 最近动态 |
```

- 「阶段」：`P5`（只写当前阶段）。
- 「已过门禁」：`对齐✅ P4✅`（只列硬门禁：对齐 / P4 / P6 / P8 / P9；产物链接写在恢复卡，不塞进台账）。
- `progress-tracker` 增加写法约定与迁移规则：已有台账无这两列 → 首次写本需求行时补列（表头 + 本行），其他行留空不改。

### A-4 `dev-session` 增加「进度判定 + 定位回执」

- 进度判定表（以产物为准，STATUS 为辅）：

| 磁盘信号 | 判定阶段 |
|---|---|
| STATUS 无条目 | P1 |
| 有条目，`design/{slug}.md` 缺 | P3 对齐前 |
| 设计文档在，无 review 报告 | P3/P4 |
| review 报告在，`design/{slug}-testcases.md` 缺 | P5 |
| 测试用例在且执行记录未填完 | P5 |
| STATUS 状态 = 待Review / 待验收 | P6–P8 |
| 状态 = 已完成但 `output/` 无报告 | P12 |

- 每阶段出口输出一行：`[P4 ✅ | 依据 review 报告 … | 下一步 P5]`，格式固定，便于压缩摘要保留。
- 信号矛盾（如有用例无 review 报告）→ 停下报告，不擅自补跑。

### A-4b `dev-session` P5「用例拟定原则」（第 0 步补充，随 A 落地，B-1 时随 P5 进入子文件）

现有第 0 步只给了 TC-1～TC-5 骨架，没有说"拟多少、拟到哪"，小模型容易按骨架机械铺满。补三条原则，写在模板之前：

1. **按实际场景拟定，不按骨架铺满**：TC-1～TC-4 每类只写本次改动真实可达的场景；有技术设计文档 / 需求文档时，用例从其「验收标准」「契约」逐条展开并标注来源条目；设计文档没有的场景不凭空补。某一类确实不适用时写 `N/A（原因）`，不编用例凑数。
2. **回归按影响面划定，不过度回归**：TC-5 的来源只认 P4 影响面分析与 `similar-issue-sweep` 扫描结果（调用方、共用组件 / Service、同表读写、同契约两端）；不在影响面内的既有功能不列入回归。回归条目标注"为什么会被波及"，说不出理由的不列。
3. **拿不准先对齐一次**：对用例是否正确、场景是否遗漏、回归范围是否过宽 / 过窄没有把握时，**在执行自测前**把用例文档摘要（各类条数 + 存疑项）给开发者确认一次，按反馈修订后再跑；不在存疑状态下直接执行、也不把疑问留到 P6 才暴露。对齐结论按规则 1 沉淀（若属纠正）。

出口条件相应补一句：用例每条可追溯到场景 / 文档条目 / 影响面依据。

### A-5 恢复卡 `.document/plan/context/{slug}.md`（每需求一张，agent 维护）

并行开发时根目录统一恢复会把别的需求的内容混进来，所以恢复内容按需求隔离：**规则先定好字段，agent 在展开任务时就把需要恢复的内容写进卡里**，压缩后只恢复自己那张。

- 建立：dev-session P1 建卡（与 STATUS 建条目同一步）；slug 与 STATUS 条目、output 报告一致。
- 更新：每次阶段迁移（定位回执输出时）同步更新；与 STATUS 一样"当下写、不等收尾"。
- 存放：项目根 `.document/plan/context/`（worktree 会话也写根目录，与 `git-commit` 8.4「进度与沉淀只写一份」一致）；每个会话只写自己的卡，天然无冲突。随 git 入库；P12 收尾后删除（归档信息已在 output 报告）。
- 固定字段（模板放 `templates/.document/plan/context/README.md`）：

```markdown
# 恢复卡：{slug}

- 需求：{一句话}　变更分级：ARCH / NORMAL
- 当前阶段：P5　下一步：{具体动作}
- 已过门禁：对齐✅(design/{slug}.md) P4✅(design/{slug}-review.md)
- 工作位置：分支 {feat/2026.10.30-xxx}；worktree {.worktree/xxx/repo 或 主工作区}；涉及仓 {backend / frontend}
- 需重读：dev-session 主文件 + references/p4-p5-review-test.md；backend/reviewer 全文（P4 时）
- 关键决策与开发者纠正（一行一条，已沉淀的注明 memory 文件）
- 未完成项 / 待确认项
```

- **不记录**：任何授权状态（提交 / 主干直提 / 计划批准）——按红线第 5 条每次重新确认。

### A-6 `common/skills/dev-session/scripts/restore_context.py`

- 定位当前需求（依次）：`--task {slug}` → cwd 在 `.worktree/{business}/…` 时取 business → 当前分支名 `{feat|opt|fix}/{date}-{business}` 取 business → 都取不到且只有一张卡则用它 → 多张卡则列出全部卡名让模型选择并提示 `--task`。
- 输出（stdout，纯文本）：
  1. `red-lines.md` 全文（找 `.claude/rules/` 或 `common/rules/`）；
  2. 本需求恢复卡全文 + STATUS 中对应行；
  3. 「需重读」清单逐项核对文件是否存在，缺的标出。
- 退出码恒 0（fail-open：缺文件时输出"未找到 X，按红线恢复协议手动恢复"）。
- 纯标准库、Python 3.8+、无第三方依赖、UTF-8 输出；从项目根或任意子目录 / worktree 内运行都能向上找到 `.document/`。
- 协议要求：压缩恢复时 / 新会话开局（iteration-planner）先运行一次。

### A-7 配套

- `project-onboarding`：A-1/A-2/B-4 安装 red-lines.md；新项目 STATUS 带两列、建 `plan/context/`；既有项目补列、补目录。
- `scripts/verify-baseline.sh`：规则层检查加 `red-lines.md`；骨架检查加 `plan/context/`。
- `iteration-planner`：开局先跑 `restore_context.py`（无 Python 时按红线手动）。
- `git-commit` 8.4：补一句"恢复卡与台账同样只写根 `.document/`"。

---

## 6. 批次 B · 主文件引导式瘦身（需团队过目）

### B-0 统一写法

- 主文件 ≤ 8KB，子文件 ≤ 8KB；主文件结构固定：
  1. frontmatter（description 不变）
  2. **约束卡**（≤ 2KB：硬门禁 + 禁止项摘要）
  3. **路由表**：阶段 / 场景 → 必读子文件 → 产物 → 出口门禁
  4. 进度判定与恢复（引用 red-lines 协议）
  5. 定位回执格式
- 子文件放 `references/`（方法论、细则）与 `templates/`（文档模板）；**每个子文件开头重复一行自己的门禁**，被单独读到时也安全。
- 子文件之间不互相引用，只由主文件路由，避免链式加载。
- 阶段切换时只读目标阶段子文件；不得"为省事一次读完所有子文件"。

### B-1 `dev-session`（试点，先做）

| 主文件保留（约 6KB） | 拆出 |
|---|---|
| 全程规则 4 条（精简版，指向 red-lines）；变更分级；**12 阶段总表**（执行者 / 子文件 / 关联技能 / 出口门禁）；进度判定与恢复；回退规则摘要 | `references/p1-p3-develop.md`（P1–P3 含文档门禁、三条路径）；`references/p4-p5-review-test.md`（P5 用例模板移 `templates/testcases.md`）；`references/p6-p8-developer-gates.md`（ARCH/NORMAL 材料模板移 `templates/`）；`references/p9-p12-closeout.md`；`references/flow-control.md`（回退与并行约定全文） |

### B-2 后端 / 前端 `reviewer`：不拆分，重排 + 隔离执行

P4 是兜底硬门禁，进入 reviewer 必须全量加载，拆分对它没有收益。改为两项：

1. **重排章节**，让压缩后保留的开头部分覆盖最关键内容：〇 七步硬流程 → 放行门禁 → 十七 漏检史 → 十五 禁止事项清单 → 十六 报告格式 → 其余维度细则。压缩若发生在 P4 中途，红线第 1 条指针要求重读全文，重排只是多一层保险。
2. **隔离执行**（降低主会话峰值的真正手段）：
   - 有子代理 / 多会话能力的宿主（Claude Code、Codex）：P4 在一个**新的子代理**中执行，只加载 reviewer 全文 + 本次 diff + 恢复卡，结论写回 `design/{slug}-review.md`，主会话只读报告。dev-session P4 增加这条路径（宿主映射：Claude Code `Agent`；Codex 子代理；无能力则主会话执行）。
   - 无子代理能力的宿主：P4 前先完成 P3 收尾与恢复卡更新，再加载 reviewer；P4 结束后不再依赖其内容，后续压缩丢掉也无妨。
- `project-onboarding`「reviewer 合并标准动作」与 📌 回注不受影响（文件结构不变）。

### B-3 `pre-dev-alignment`

| 主文件保留（约 9KB） | 拆出 |
|---|---|
| 技术栈判断；任务分级；L1/L2/L3 流程骨架 + 门禁；落档规则摘要；Skill 链路指引 | `templates/requirement-doc.md`、`templates/tech-design-doc.md`、`templates/l1-plan.md`；`references/risk-precheck.md`（第零步细则）；`references/pre-dev-checklist.md`；`references/semantic-guide.md` |

### B-4 `git-commit`

| 主文件保留（约 8KB） | 拆出 |
|---|---|
| 一 授权与铁律；2.1 决策表；2.4 / 2.5 / 2.6 硬性节；三 前缀；四 格式；七 自检摘要 | `references/branch-naming.md`（2.2、2.3）；`references/examples.md`（五）；`references/worktree.md`（八） |

### B-5 `yzj-dev-workflow`

- 第 6 节「完整研发流程总览」**删除**（3.5KB）。核对结论：流程框图的步骤是 dev-session 12 阶段的子集；"按关注点调用哪个 backend 技能"的列表与本技能第 8 节「Skill 引用速查表」逐项重复；4 条关键控制点都是 dev-session 已有门禁。原位留两行："完整研发流程见 dev-session（12 阶段 + 门禁）；编码中按关注点调用的 backend 技能见第 8 节"。
- 速查（3、4）与自检（5）移 `references/`；主文件保留 0 编码前门禁、1 架构概览、2 场景路由、7 禁止事项、8 引用表（约 10KB）。

### B-6 `scripts/check-skill-layout.sh`

- **告警（不阻断）**：主文件 > 8KB、子文件 > 12KB；主文件缺约束卡标题。阈值只作提醒——规则随能力累积会增长，不做硬限制。
- **失败（阻断发布）**：路由表指向的文件不存在；`references/`、`templates/` 下无主文件引用的孤立文件；子文件开头缺门禁行。
- 纳入发布流程。

### 预期效果

单阶段上下文峰值（P4 以外）：约 150KB → 约 45–50KB；P4 峰值靠子代理隔离解决；压缩后重读范围：一整个大文件 → 主文件 + 一个子文件（P4 为 reviewer 全文）。

---

## 7. 批次 C · 机械兜底

| 机制 | 通用层 | 宿主适配 |
|---|---|---|
| 提交信息检查 | `common/skills/git-commit/scripts/commit_guard.py`：作为 git `commit-msg` hook，拒绝 AI 记号（`Co-Authored-By: Claude`、`Generated with`、模型名）与进度词；读 UTF-8 文件传参。项目提交 `.githooks/commit-msg`（调用该脚本），onboarding 设 `core.hooksPath=.githooks` | — |
| 主干直提 | `commit_guard.py --precheck`：在主干上输出授权提醒（exit 0） | Claude Code：`PreToolUse`（Bash，`if: Bash(git commit *)`）→ 主干时返回 `ask` + 原因；AI 记号直接 `deny` |
| 压缩后重注入 | `restore_context.py`（批次 A） | Claude Code：`SessionStart`（matcher `compact`）调用它（hook 环境下无分支 / worktree 线索时输出全部卡名）。Codex：**先实机核实**（见下），核实后另起一批接入 |
| 分发 | 脚本在技能目录内，随复制 / 插件走 | 插件：`common/hooks/hooks.json`（`${CLAUDE_PLUGIN_ROOT}/skills/.../*.py`）；复制安装：`templates/plugins/claude-settings.json` 增 hooks 片段（`$CLAUDE_PROJECT_DIR/.claude/skills/.../*.py`）；`check-plugin-manifests.sh` 校验 hooks.json 指向的脚本存在 |

- 所有 hook fail-open（脚本异常 → 放行并提示），不让流程工具故障阻塞开发。
- `python` / `python3` 命令名差异：hook 命令用 `python`，README 注明 Windows / macOS 环境要求。

**Codex 核实清单（批次 C 前完成，结果记 `reports/`）**：
1. 当前团队使用的 Codex CLI 版本是否支持 hooks（`hooks.json` / `config.toml`），有哪些事件（PreCompact / PostCompact / 会话启动类）；
2. 压缩后 AGENTS.md 是否从磁盘重读（构造长会话触发压缩，检查入口文字是否仍在）；
3. 显式引用的 `common/rules/*.md` 压缩后是否保留；
4. 子代理 / 多会话能力是否可用于 P4 隔离。
核实结论决定 Codex 侧用 hook 自动注入，还是只靠入口文字协议 + `restore_context.py` 手动运行。

---

## 8. 批次 D · 验证

1. 构造用例：在 Codex、经 Claude Code 接入的 DeepSeek 上，加载流程 → 手动触发压缩（`/compact` 或填满上下文）→ 推进到 P4 / P9 / P11。
2. 观察指标：是否重读章节、是否跳 P4、是否在无授权下 commit、是否继承主干授权、是否输出定位回执。
3. 对比改动前（基线 2026-10-30）与各批次后结果，记录到 `reports/`。
4. 批次 B 另验：`verify-baseline.sh` 对拆分后目录的判读；`project-onboarding` B 流程对拆分 reviewer 的合并。

---

## 9. 发布与提交

- 每批一次提交 + 一次基线：README「当前基线」→ 六份 `plugin.json` version → `check-plugin-manifests.sh` → `check-skill-layout.sh`（B 起）→ `claude plugin validate .`。
- 批次 B 的五个技能分 5 个提交（dev-session 试点先行，团队过目后再做其余四个）。
- commit 按 `git-commit` 规范，不留 AI 记号。

---

## 10. 核对记录（2026-10-30 第二轮）

| # | 原问题 | 结论 |
|---|---|---|
| 1 | 红线是概括还是指针 | 指针式：结论 + → 原章节；恢复协议门禁前重读原文（决策 8） |
| 2 | STATUS 阶段列格式 | 拆两列「阶段」「已过门禁」（决策 9） |
| 3 | 根目录统一恢复在并行时对不上 | 每需求一张恢复卡，agent 展开任务时建立、阶段迁移时更新；脚本按分支 / worktree / `--task` 定位（决策 10） |
| 4 | reviewer 按需加载维度 | 否决：P4 全量加载；改为重排 + 子代理隔离（决策 11） |
| 5 | 删 yzj-dev-workflow 第 6 节 | 第二轮改为**删除**：逐项核对确认已被 dev-session 与本技能第 8 节覆盖（决策 12） |
| 6 | git hook 对人也生效 | 接受 |
| 7 | 子文件阈值 | 只告警不阻断，不做硬限制（决策 13） |
| 8 | `common/hooks/` 位置 | 按推荐：插件根，不在 `common/skills/` 下 |
| 9 | Codex 适配 | 先实机核实，核实后另起一批（决策 14） |
| 10 | 批次顺序 | A → B（dev-session 试点）→ C → B 其余 → D（决策 15） |

**第三轮补充**：P5 用例拟定原则三条（A-4b，决策 16）。

**仍待确认**：
- 恢复卡在 P12 收尾后删除，还是保留到归档？（推荐删除：output 报告已含全部信息，避免 `plan/context/` 堆积）
- P4 子代理隔离在 Claude Code 上的落地形态：dev-session 正文写"启动子代理执行 reviewer"即可，还是需要一份固定的子代理 brief 模板（推荐先写正文规则，模板视试点效果再加）。

---

## 11. 文件级改动清单（汇总）

| 批次 | 新增 | 修改 |
|---|---|---|
| A | `templates/common/rules/red-lines.md`；`templates/.document/plan/context/README.md`（恢复卡模板）；`common/skills/dev-session/scripts/restore_context.py` | `AGENTS.md`；`templates/AGENTS.md.template`；`templates/CLAUDE.md.template`；`templates/common/rules/collaboration.md`；`templates/.document/plan/STATUS.md`（两列）；`common/skills/dev-session/SKILL.md`（建卡 / 进度判定 / 回执 / P5 用例拟定原则）；`common/skills/progress-tracker/SKILL.md`；`common/skills/iteration-planner/SKILL.md`；`common/skills/project-onboarding/SKILL.md`；`common/skills/git-commit/SKILL.md`（8.4 一句）；`scripts/verify-baseline.sh`；`README.md` |
| B | dev-session / pre-dev-alignment / git-commit / yzj-dev-workflow 的 `references/*.md`、`templates/*.md`；`scripts/check-skill-layout.sh` | 四个 SKILL.md 主文件；`backend/reviewer/SKILL.md`、`frontend/reviewer/SKILL.md`（仅重排章节）；`common/skills/dev-session`（P4 子代理路径）；`scripts/verify-baseline.sh` 提示文案；`README.md` |
| C | `common/skills/git-commit/scripts/commit_guard.py`；`templates/.githooks/commit-msg`；`common/hooks/hooks.json`；`backend/hooks/`、`frontend/hooks/`（如需） | `templates/plugins/claude-settings.json`；`common/skills/git-commit/SKILL.md`；`common/skills/project-onboarding/SKILL.md`（hooksPath）；`scripts/check-plugin-manifests.sh`；`README.md` |
| D | `reports/2026-xx-xx-compaction-validation-*.md` | — |
