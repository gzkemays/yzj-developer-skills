---
name: iteration-planner
description: >
  持续迭代开发规划。每次开启新 session 时触发，帮助 AI 了解当前需要开发的内容、背景和上下文，
  识别并行中的需求，并引导复用已有的业务 SKILL 与能力登记册进行开发。
  当用户说"开始开发"、"继续开发"、"新的迭代"、"接着做"、"下一步做什么"、"今天做什么"，
  或在 session 开始时需要了解项目当前状态和开发方向时触发。
---

# 持续迭代开发规划（iteration-planner）

本 SKILL 确保每次新 session 都能快速对齐开发上下文，避免重复沟通、避免与并行需求冲突。

---

## 一、执行流程

### Step 1：读取需求台账（必做第一步）

读取 `.document/plan/STATUS.md`：

- **进行中**的需求有哪些、各自状态（开发中/待Review/待验收）与最近动态
- **容量检查**：进行中条目 > 20 → 按 `progress-tracker`「台账容量治理」红线 1 向开发者输出裁决清单（标记 30 天无动态的疑似弃用项），**裁决完成前不开新需求**
- 是否有**待恢复**的搁置需求
- 上一个 session 的需求是否卡在某个门禁阶段（待Review/待验收 → 优先推动收尾而非开新需求）

### Step 2：读取计划总览

读取 `.document/plan/00-plan-overview.md`，获取当前迭代阶段与各阶段状态。

### Step 3：扫描当前阶段的模块文档

读取当前阶段对应的模块文档，统计各模块完成率（已勾选 / 总任务数），识别下一个应开发的模块。

### Step 4：检查近期开发活动

`git log --oneline -20` 了解上次 session 做了什么、是否有未完成的工作；
对照 `.document/developer/output/` 最近的开发报告确认遗留事项。

### Step 5：生成开发简报

```
## 📋 开发简报

**当前阶段**: P{N} - {阶段名称}　**阶段进度**: {完成}/{总数}

### 并行需求（来自台账）
| 需求 | 状态 | 最近动态 |
|------|------|----------|

### 各模块状态
| 模块 | 后端进度 | 前端进度 | 状态 |

### 上次开发内容
- {git 提交摘要 + output 报告遗留事项}

### 建议本次开发
- **模块**: {推荐}　**原因**: {依赖满足/连续性/收尾优先}
- **关键任务**: {3-5 个未完成任务}
- **冲突提示**: {与进行中需求的模块重叠，如有}
```

### Step 6：确认开发方向

询问用户按建议开发还是另有优先事项。确认后进入 `dev-session` 流程（P1 起）。

### Step 7：加载相关 SKILL 与能力

- 后端任务 → backend skills（project-structure / model-conventions / service-conventions / controller-conventions / mybatis / integration-flow / cache / security / grpc / tabledef / common / logging / reviewer）
- 前端任务 → frontend skills（view-conventions / i18n-automation / reviewer）+ 项目级 skill
- 读 `.document/developer/capability/CAPABILITY.md`，将可复用能力带入开发计划

---

## 二、判断当前阶段的规则

1. 读 `00-plan-overview.md` 阶段状态：`已完成` 跳过、`进行中` 即当前阶段
2. 所有已开始阶段都完成 → 推进到下一个 `未开始` 阶段
3. 一个阶段的所有模块完成时，提醒用户更新阶段状态

## 三、模块推荐优先级

1. **收尾优先**：台账中卡在待Review/待验收的需求先推动闭环
2. **依赖满足**：前置依赖模块已完成
3. **连续性**：优先与上次 session 相关的模块
4. **前后端对称**：某模块单侧完成时优先补齐另一侧
5. **避让并行**：与进行中需求模块重叠的，提示冲突后由用户决定
6. 同等条件下按文档编号顺序

## 四、新增业务 SKILL

开发中发现可复用的模式或规范时：

1. 按 `capability-registry` 登记到能力登记册（轻量、必做）
2. 模式足够通用且复杂时，用 `skill-creator` 升级为正式 SKILL：前端放前端仓库 `.claude/skills/`，后端放后端仓库 `.claude/skills/`
3. 跨项目通用的 → 登记「待反哺 framework」

## 五、注意事项

- 不要在用户未确认前就开始写代码
- 发现计划文档与实际代码状态不一致（文档未勾选但代码已存在）→ 提醒用户并按 `progress-tracker` 修正
- 每次 session 结束前按 `progress-tracker` 更新进度（dev-session P9 强制）
