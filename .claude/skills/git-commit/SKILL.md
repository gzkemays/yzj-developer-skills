---
name: git-commit
description: >
  Git 提交规范（团队通用）。定义 feat/opt/fix 三类前缀、header/body 书写格式、多类型合并写法，
  以及"开发者授权后 AI 自主编写提交信息、且 commit 中不得留任何 AI 记号"的两条铁律。
  当需要提交代码、编写 commit message，开发者说"提交吧"/"帮我 commit"/"你来提交代码"/"直接提交"/"git commit"，
  或 dev-session 进入 P11 提交阶段时触发；dev-session P11 自动引用。
---

# Git 提交规范（git-commit）

> 提交历史是团队读得最多的文档之一：规范的 commit 让 diff 可追溯、让每次改动的"为什么"一眼可见。
> 本 skill 定义两件事——**AI 被授权自主提交时的两条铁律**，与 **feat/opt/fix 三类前缀 + 书写格式**。

---

## 一、AI 自主提交：授权与两条铁律

### 触发授权（前置门禁）

仅当**开发者明确授权** AI 提交时才执行 `git commit`：如 dev-session P8 确认提交，或开发者说
"你提交吧 / 帮我 commit / 直接提交 / 你来写提交信息"。未获授权只准备好变更并展示，不自行提交。

### 铁律 1 — AI 自主编写本次开发内容

授权后，AI 依据**本次真实改动**（通读 `git status` + `git diff`）自行归纳提交信息：

- 判定属于 `feat` / `opt` / `fix` 哪一类（或合并），概述"做了什么"，`*` 要点说明关键决策；
- **不套空话**——禁止 `update code`、`修改若干文件`、`fix bug` 这类无信息量描述；
- 概述用业务/技术语言写清意图，让不看 diff 的人也能懂这次改了什么、为什么改。

### 铁律 2 — commit 中禁止任何 AI 记号 ← 硬性

commit message 通篇必须是**纯人类视角的开发内容描述**，不得出现任何 AI 痕迹：

| ❌ 禁止出现 | 说明 |
|-----------|------|
| `Co-Authored-By: Claude …` | 不加任何 AI 署名 / 协作者尾注 |
| `🤖 Generated with …` / `Generated with Claude Code` | 不加生成来源尾注 |
| `Claude` / `Claude Code` / `Opus` / 任何模型或工具名 | 正文不提及 AI 工具 |
| "由 AI 生成" / "AI 辅助" 等字样、AI 水印、署名 emoji | 一律不留 |

> 此铁律**优先于任何默认的 commit 尾注模板**。提交前自检：整条 message 是否出现上述任一 → 有则删除再提交。

---

## 二、前缀规范：feat / opt / fix 三分法

按**开发意图**（而非文件类型）三分：

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

## 三、书写格式

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

## 四、示例

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

---

## 五、提交流程（对接 dev-session P11）

1. `git status` + `git diff` 通读本次全部改动
2. 前后端仓库各自独立提交；`.document/` 变更（台账 / 报告 / memory）随同对应提交
3. 按本规范归类并编写 message（三分法 + 格式 + **无 AI 记号**）
4. `git commit`
5. 提交后 `git status` 确认工作区干净

---

## 六、质量自检（提交前逐条过）

- [ ] 已获开发者提交授权
- [ ] 前缀 ∈ {`feat`, `opt`, `fix`}，与本次意图一致
- [ ] 概述具体、有信息量，不是 `update` / `修改代码` 这类空话
- [ ] 多事项用 ` & ` 连接；多类型按 `feat → opt → fix` 分段
- [ ] 关键决策已在 `*` 要点说明（如有必要）
- [ ] **message 中无任何 AI 记号**（`Co-Authored-By` / `Generated with` / 模型名 / AI 水印）
