# git-commit · 附录：Worktree 隔离开发（并行迭代防冲突 / 防进度脱节）

> 门禁：worktree 必须放项目根 `.worktree/{business}/{repo}`；进度、恢复卡与沉淀只写项目根 `.document/`；删除前先拆链接。

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

- 建树命令：`git -C {repo} worktree add {project-root}/.worktree/{business}/{repo} -b {feat|opt|fix}/{yyyy.MM.dd}-{business}`（自当前主干切出，分支名按 2.2——主文件路由表「切开发分支」）
- worktree 是**单仓**检出：纯后端 / 纯前端只建对应那一个；全栈各建各的，互不影响
- 编辑任一仓文件时祖先链含：该仓技能层（前 / 后端规范）+ 根技能层（流程）+ 根 `.document/`（Claude Code 下技能层即各级 `.claude/`；其他宿主为入口文件声明的技能目录）→ 规则与技能全识别
- `.worktree/` 必须进项目根 `.gitignore`（单仓项目尤其注意，否则整棵树会被当成未跟踪文件）
- 多需求并行各用各的任务目录与分支（同一仓同一分支只能在一个 worktree 检出）
- **树内一切命令以树内仓目录为 cwd**：构建 / 测试 / 校验命令不用项目根相对路径——项目入口文件里 `cd {backend-repo} && mvn …` 这类命令在 worktree 会话里要按 `{project-root}/.worktree/{business}/{repo}` 解析，否则编译 / 测试的是主工作区那棵树；跨仓引用写 `../{repo}`，镜像结构保证它在根与树内都指向同一需求的另一棵树

### 8.3 Windows 路径上限（260）——后端仓必做

后端 Java 包路径深，嵌套一层任务目录后最深文件容易超过 Windows MAX_PATH。**建树前对该仓执行一次 `git config core.longpaths true`**，否则 `git worktree add` 报 `Could not reset index file to revision 'HEAD'`。开启后 git 与读写 / 编辑工具均能正常处理深路径文件。

### 8.4 进度与沉淀只写一份（关键）

- `.document/` 全项目只有项目根这一份：台账 `STATUS.md`、恢复卡 `plan/context/{条目名}.md`、plan / design / 用例文档、memory、能力登记**一律写项目根**，**绝不写进 worktree 内的副本**——单仓项目的 worktree 会自带一份 `.document/` 副本，最容易写错地方 → 进度永不在多棵树间分叉（`dev-session/scripts/restore_context.py` 在 `.worktree/` 内运行时也按此取项目根）
- 每完成一个任务**即时**按 `progress-tracker` 回填，并在 worktree 内**分段提交**（每个可独立 review 的语义单元一次；每段都按 `git-commit` 主文件一「授权范围」取得授权，分段不是独立授权），不长期囤大量未提交改动
- 开树时在台账该条目「最近动态」记一行：worktree 路径 + 分支名 + 所属仓，避免跨会话丢失上下文
- **个人 memory 不跨树**：个人 memory（Claude Code：`~/.claude/projects/`；其他宿主：用户配置的位置）按 cwd 路径分桶，worktree 会话与主工作区会话读到的不是同一份——需求上下文、纠正、踩坑一律按 `team-memory` 写根 `.document/developer/memory/`，不要靠个人 memory 在树之间传递
- **多会话同写根 `.document/`**（台账、索引、能力登记）→ 按 `progress-tracker`「并行开发的文档冲突约定」：写前重读、只改自己的行、写完随已获授权的提交入库；追加型文件冲突双方保留；结构化文档单一写者

### 8.5 提交、合并与收尾

- 提交推送按 2.3 默认流程（主文件路由表「切开发分支」）：在 worktree 内 `commit` → `push -u origin {分支名}` → 创建 MR → 交接四项
- 基线漂移：主干推进较多时**如实告知开发者**，是否 `rebase` 由开发者决定（AI 不自动变基，同 2.3 默认流程）
- 收尾由开发者完成：合并 MR → `git worktree remove .worktree/{business}/{repo}`（先按 8.6 拆掉链接）→ 删除已合并分支（AI 不删分支，见 2.6；开发者明确要求时 AI 可代执行 `git worktree remove`）
- 迁移既有未提交改动进 / 出 worktree：`git diff -- <file> > x.patch` + `git -C <tree> apply x.patch`，**不要整仓 stash**——stash 会把他人改动一起带走

### 8.6 删除前先拆链接（防连带删主工作区）

worktree 里为了跑构建，常从主工作区借依赖目录（Windows 目录联接 `mklink /J`、Unix 符号链接 `ln -s`，如 `node_modules`）。在 Windows 上，`git worktree remove`、`rm -rf`、`Remove-Item -Recurse` 可能顺着联接递归进**主工作区**删除：源码不受影响，但依赖目录会残缺。实例：删掉了主工作区的 `node_modules/.modules.yaml` 和 `.pnpm` 下的部分包，碰到 workspace 包之间的循环联接报 `Filename too long` 才停下。固定顺序：

1. 列出 worktree 内所有链接，遇到链接只记录、不进入：Windows 用 PowerShell 逐层枚举，条目带 `ReparsePoint` 属性就记录、不再往下递归（不要用会跟随联接的递归命令，循环联接会无限深入）；Unix `find <worktree> -type l`
2. 逐个只删链接本身：Windows `rmdir <链接>`（不带 `/s`）；Unix `rm <链接>`（不带 `-r`，链接名末尾不加 `/`）
3. 复查确认已无链接，再执行 `git worktree remove`
4. 删除中途报 `Filename too long` 时，worktree 可能已从 git 注销、目录还残留：先回到第 1 步确认没有链接，再用 `\\?\<绝对路径>` 前缀删除残留目录；随后检查主工作区依赖目录是否完整（如 pnpm 用 `install --frozen-lockfile --offline` 从本机 store 补回，再跑一次类型检查）
