# git-commit · 开发分支命名与默认提交流程（2.2 / 2.3）

> 门禁：分支名 `{feat|opt|fix}/{yyyy.MM.dd}-{business}`，日期取系统当天；流程中暂存只 `git add -- <显式路径>`，推送后输出交接四项；主干直提与禁止动作见主文件 2.5 / 2.6。

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
