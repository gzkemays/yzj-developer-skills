---
name: code-reviewer
description: 前端代码审查 skill（Vue 3 + TypeScript 技术栈）。当用户要求 review 前端代码、审查页面/组件规范、检查前端代码质量，或 dev-session P4 AI Review 阶段触发时使用。审查范围覆盖：类型对齐后端契约、i18n 完整性、设计系统 token、数据展示工具方法、表单校验对齐、组件规范、API 调用约定。按七步硬流程执行，逐维度 × 逐文件全覆盖，禁止选择性抽查。
---

# 前端代码审查规范

本 skill 与 backend `reviewer` 等价对位：后端有硬性审查流程，前端同样有。
规范权威来源：`view-conventions` skill + 项目前端 `CLAUDE.md`（设计系统、契约约定）+ 项目 memory 中的前端踩坑记录。

> **为什么前端也要硬流程**：历史教训表明，前端漏检集中在"机器可查但目测会漏"的项——硬编码颜色、
> i18n key 路径写错、类型多出后端不存在的字段、表单校验与后端 @Size 不一致。这些必须靠 Grep 扫描兜底。

---

## 〇、七步硬流程（任何前端 Review 必须按此执行）

**Step 0 — 装载规则**：Read 前端仓库 `CLAUDE.md` 全文（不许凭记忆）+ Read 项目 memory 中前端相关 tech/feedback 条目（如组件库踩坑、受控组件陷阱）。
进入审查前必须在输出中明确写一句：**"已 Read 前端 CLAUDE.md + 相关 memory（{日期}），按 {N} 文件 × 全维度矩阵审查。"** 未写此句即开始 review = 违反协议 = 必返工。

**Step 1 — 圈定范围**：列出本次 `git status` / `git diff` 中所有新建 + 修改的 `.vue` / `.ts` / `.d.ts` 文件，输出清单。全部进入审查范围。

**Step 2 — 强制 Grep 扫描**（对每个 `.vue` / 样式文件）：

| 扫描目标 | Grep 模式 | 规则 |
|----------|-----------|------|
| 硬编码颜色 | `#[0-9a-fA-F]{3,8}\b`、`rgb\(` | 必须用项目设计系统 token（`var(--{prefix}-*)`），variables 定义文件除外 |
| i18n key 路径错误 | `\$t\('common\.(cancel\|confirm\|ok\|save\|delete\|edit\|create\|search\|reset)'\)` | 通用操作应为 `common.action.*`（按项目 key 策略） |
| 硬编码用户可见文案 | 中文字面量出现在 template/消息调用中 | 必须 i18n 化（详查用 `i18n-automation`） |
| 残留调试 | `console\.log\(` | 移除（保留有意为之的 warn/error） |
| 未使用 import / 未注册 emit | 构建告警 + 目测确认 | 移除 |

**Step 3 — 类型契约检查**（每个 `.d.ts` / typings 文件）：

- 前端 `XxxVO` / `XxxOperate` / `XxxQuery` 字段是后端对应类字段的**子集**——Grep 后端 Java 文件交叉验证，不能多出后端不存在的字段
- **EntityId 精度**：雪花 ID 字段保持 `string`，不被 `Number(...)` 转换（精度丢失）
- 布尔字段命名与后端对齐（`xxxFlag`，不用 `isXxx`）

**Step 4 — service / API 层检查**（每个 `src/service/api/*.ts`）：

- 写操作返回类型：创建 `EntityId`/`number`，更新/删除 `boolean`——**禁止 `Void`**（`CommonResult<Void>` 的 data 为 null，`if (res.data)` 永远 falsy）
- Void 接口（登录等）用 `code` 判断成功，不用 `res.data`
- 大字段（LONGTEXT，如 contentJson）在 service 层做 string ↔ object 转换，组件不感知
- 分页接口返回字段（list / total / pageNo / pageSize）解析正确

**Step 5 — 组件与表单检查**（每个页面/组件）：

- 文本列使用 `displayText()`、时间列使用 `formatDateTime()`（或项目约定的等价工具），null/空白 → `'-'`
- 表单 `:maxlength` + `formRules.min/max` 与后端 `@Size` 一致；`required` 与 `@NotBlank` 一致
- 成功提示使用项目统一通知工具（如 `notifySuccess`），不直接 `window.$message`
- 受控组件 / 组件库已知陷阱：核对 memory 中的组件库踩坑条目（如嵌套 Drawer mask 残留、Tabs 惰性渲染等）

**Step 6 — 按第四节标准格式输出报告**：逐维度给结论。

**Step 7 — 自修后复检**：修复后**重跑 Step 2 ~ Step 6**，验证无回归。

### 同类违规回溯（与 `similar-issue-sweep` 联动）

每发现一处违规，立即在本次变更全部文件中扫描同一模式；属于漏检史条目的，扩大到所在模块全量文件。

---

## 一、审查维度与规则来源

```
┌────────────────────────────────────────────────────────────┐
│  1. 类型契约对齐    → Step 3 + api-contract-checker 规则 3   │
│  2. API 调用约定    → Step 4 + view-conventions 第五节       │
│  3. i18n 完整性     → Step 2 + i18n-automation               │
│  4. 设计系统 token  → Step 2 + 项目 CLAUDE.md                │
│  5. 数据展示工具    → Step 5 + 项目 CLAUDE.md                │
│  6. 表单校验对齐    → Step 5 + api-contract-checker 规则 4   │
│  7. 页面/组件结构   → view-conventions（结构、BEM、hooks）    │
│  8. 组件库陷阱      → 项目 memory（tech-* 条目）              │
└────────────────────────────────────────────────────────────┘
```

**全覆盖要求**：禁止选择性 Review；每个被审文件过一遍适用维度，报告逐维度给结论。

---

## 二、禁止事项清单

| # | 禁止事项 | 严重程度 |
|---|----------|----------|
| 1 | 前端类型定义包含后端不存在的字段 | 🔴 严重（运行时 undefined） |
| 2 | 写操作 API 按 `CommonResult<Void>` 处理（`if(res.data)` 判断 Void 接口） | 🔴 严重（静默失败） |
| 3 | 雪花 ID 用 `number` 承载或 `Number()` 转换 | 🔴 严重（精度丢失） |
| 4 | 硬编码颜色绕过设计系统 token | 🟡 警告 |
| 5 | 用户可见文案硬编码不走 i18n | 🟡 警告 |
| 6 | i18n key 路径不符合项目策略（如 `common.cancel` 应为 `common.action.cancel`） | 🟡 警告 |
| 7 | 文本/时间列不使用 `displayText` / `formatDateTime` | 🟡 警告 |
| 8 | 表单校验规则与后端 `@Size` / `@NotBlank` 不一致 | 🔴 严重（提交被拦截或脏数据） |
| 9 | 大字段未在 service 层转换，组件直接处理原始字符串 | 🟡 警告 |
| 10 | 成功提示直接 `window.$message` 绕过统一通知工具 | 🟡 警告 |
| 11 | 残留 `console.log` / 未使用 import / 未注册 emit | 🟢 提示 |
| 12 | 样式不加 `scoped` 或不按 BEM 命名 | 🟡 警告 |
| 13 | 表格类名/样式硬依赖组件库内部实现（版本升级即碎） | 🟡 警告 |
| 14 | 翻新公共组件未评估引用方影响 | 🔴 严重 |

---

## 三、自测衔接（Review 通过后）

Review 通过 ≠ 自测通过。进入 dev-session P5：

- 构建验证：`npx vite build`（含类型检查；项目如有 `vue-tsc` 问题以 CLAUDE.md 说明为准）
- 推荐用 Claude Preview MCP 做渲染/交互/网络验证（dev-session P5 两轮机制）

---

## 四、审查报告格式

```markdown
## 前端代码审查报告

### 协议确认
已 Read 前端 CLAUDE.md + 相关 memory（{日期}），按 {N} 文件 × 全维度矩阵审查。

### 审查范围
[文件清单]

### 逐维度结论
| 维度 | 结论 |
|------|------|
| 类型契约对齐（含后端交叉验证） | ✅ / ❌ N 处 |
| API 调用约定（返回类型/Void/大字段） | ✅ |
| i18n（key 路径 + 硬编码扫描） | ✅ |
| 设计系统 token（硬编码颜色扫描） | ✅ |
| 数据展示工具 / 表单校验对齐 | ✅ |
| 页面结构 / BEM / hooks | ✅ |
| 组件库陷阱（memory 专项核对） | ✅ |

### 问题汇总（如有）
| 序号 | 严重程度 | 维度 | 文件位置 | 问题描述 |

### 问题详情
（违规代码 + 规范出处 + 修复建议 + 同类扫描结果）

### 审查结果：✅ 通过 / ❌ 不通过 → 自修后重跑 Step 2-6
```

---

## 五、漏检史清单（每次 Review 必须主动核对）

> 登记曾被开发者捕获的前端漏检项；项目新增漏检按 `team-memory` 升级机制当场追加到项目级清单。

| Rule | 出处 | 教训来源 |
|------|------|----------|
| 硬编码颜色违反设计系统 token | 禁止 #4 | 曾漏检 |
| i18n `common.cancel` 路径错误 | 禁止 #6 | 曾漏检 |
| 类型多出后端不存在的字段 | 禁止 #1 | 曾因未交叉验证后端 Java 文件漏检 |
| 嵌套抽屉/弹窗 mask 残留等组件库陷阱 | 维度 8 | 曾漏检——必须核对 memory 条目而非凭印象 |
| 表单校验与后端 @Size 不一致 | 禁止 #8 | 曾漏检 |
