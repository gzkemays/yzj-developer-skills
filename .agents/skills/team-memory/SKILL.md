---
name: team-memory
description: "团队共享开发记忆体系。定义 .document/developer/memory/ 的目录结构、文件格式、命名规范、 索引维护与「纠正即沉淀」硬规则，让纠错、踩坑、架构决策、项目状态随代码入库、跨会话跨成员生效。 当需要记录开发者反馈、沉淀技术踩坑、记录架构决策、更新项目状态，或开发者说\"记一下\"、 \"沉淀一下\"、\"别再犯了\"、\"上次说过\"时触发；dev-session 全程及 P2/P10 阶段自动引用。"
---

# 团队共享记忆体系（team-memory）

> 个人偏好存个人 memory（`用户明确配置的个人记忆位置`）；**团队应共享的认知**存本体系，随代码提交入库，
> 所有成员的 AI 会话都能读取。记忆的价值在于"下次不再犯、下次不用再说"。

---

## 一、目录结构与文件格式

```
.document/developer/memory/
├── MEMORY.md              # 索引（每条记忆一行，必须维护）
├── feedback-*.md          # 开发者反馈与强约束（纠正、否决、规范提醒）
├── tech-*.md              # 技术踩坑与解法（框架限制、边界条件、集成经验）
├── project-*.md           # 项目状态与决策（进行中事项、历史对齐、阶段结论）
└── {topic}.md             # 参考类（架构说明、体系文档等，无前缀）
```

每个文件 = 一个主题，frontmatter 固定：

```markdown
---
name: feedback-xxx-yyy
description: "一句话摘要——索引和回忆时靠它判断相关性，写清楚触发场景"
metadata:
  node_type: memory
  type: feedback | tech | project | reference
---

正文
```

**正文要求**（feedback 类必含）：

1. **开发者原话**：引用纠正时的原始表述（带日期），这是约束力的来源
2. **Why**：为什么这是规则——错误造成了什么后果
3. **How to apply**：下次遇到什么信号、该怎么做（可执行，不是感想）
4. 关联记忆用 `[[name]]` 互链

---

## 二、纠正即沉淀（硬规则）

### 触发条件（命中任一 → 必须当场写入，不等收尾阶段）

| # | 信号 | 类型 |
|---|------|------|
| 1 | 开发者**纠正/否决** AI 的方案、代码、流程（"不对"、"不要这样"、"我说过"） | feedback |
| 2 | 开发者给出**通用性约束**（"以后都…"、"凡是…必须…"） | feedback |
| 3 | **同一问题第二次出现**（无论谁发现）——说明第一次没沉淀或沉淀无效 | feedback（升级） |
| 4 | 排查超过 30 分钟的**非显而易见踩坑**（框架行为、隐式约定、环境陷阱） | tech |
| 5 | 影响后续开发的**架构/方案决策**拍板（含"暂不做"的决定） | project（重大的另写 ADR） |
| 6 | 前后端**契约新增或变更** | tech / 项目 AGENTS.md |

### 执行顺序（固定）

```
完成本次修正 → 立即写入/更新 memory 文件 → 更新 MEMORY.md 索引
→ 在响应中告知开发者："已沉淀至 memory：{文件名}"
```

**反模式**：
- "我记住了"但没写文件 —— 会话结束即遗忘，等于没记
- 攒到 P10 一起写 —— 中途 session 中断就全丢了
- 只写"发生了什么"不写"下次怎么做" —— 无法执行的记忆不拦截重犯

### 重复犯错的升级机制

同一条 feedback 第二次被违反时：

1. 在该 memory 中追加**违反记录表**（日期 + 场景）
2. 把该项加入对应 reviewer（backend / frontend）的**漏检史清单**，使其成为 Review 必查项
3. description 中加 **强约束** 标记，MEMORY.md 索引行加粗

---

## 三、MEMORY.md 索引维护

按类型分节，每条记忆一行：

```markdown
# {项目名} Shared Developer Memory

> 团队共享技术沉淀，随代码入库。个人偏好仅存入用户已配置并授权的位置；未配置时不创建宿主私有目录。

## Development Constraints（feedback 类）
- [标题](feedback-xxx.md) — 一句话钩子（强约束加粗整行）

## Technical Lessons（tech 类）
- [标题](tech-xxx.md) — 一句话钩子，含关键结论（让读索引就能避坑）

## Project Status（project 类）
- **[标题](project-xxx.md)** — 状态 + 出口条件（进行中的加粗）

## Reference
- [标题](xxx.md) — 用途
```

**索引行的钩子要写"结论"而非"主题"**：`mybatis-flex updateById 默认忽略 null，置 NULL 必须用 UpdateChain.set` ✅；`关于 mybatis-flex 的一些坑` ❌。

---

## 四、读取时机（与 dev-session 对应）

| 时机 | 动作 |
|------|------|
| P2 加载沉淀 | 读 MEMORY.md → 按任务关键词命中条目**读全文**；feedback 强约束必读 |
| P3 编码前 | 涉及域有 tech/feedback 记忆的，编码遵循其 How to apply |
| P4 Review | reviewer 漏检史与 feedback 强约束作为必查项 |
| 回忆有时效 | 记忆反映写入时的状态——引用的文件/方法/开关，使用前确认仍存在 |

---

## 五、记忆卫生（防止索引腐烂）

- **写前查重**：先搜 MEMORY.md 是否已有同主题条目 → 更新原文件而非新建重复文件
- **并行写索引**：MEMORY.md 是追加型文件，多会话 / 多 worktree 同时加行时写前重读、只加自己的行、写完即提交；合并冲突双方都保留（见 `progress-tracker`「并行开发的文档冲突约定」）；个人 memory 按 cwd 分桶、不跨 worktree，团队要共享的只认本体系
- **过时即清**：开发使既有记忆失效时（接口废弃、约束解除），更新或删除该记忆及索引行；项目状态类记忆完成后标记 ✅ 或移除"进行中"加粗
- **拆分过长**：单文件超过一屏且含多个独立主题时拆分，索引分别登记
- **不存代码已说明的事**：代码结构、git 历史、AGENTS.md 已有内容不重复入 memory

---

## 六、与其他沉淀渠道的分工

| 内容 | 去处 |
|------|------|
| 开发者纠正、踩坑、约束 | 本体系（memory） |
| 可复用的组件/工具/流程 | `capability-registry`（能力登记册） |
| 重大架构决策（含权衡过程） | `.document/adr/`（memory 中放一行指针） |
| 需求进度 | `.document/plan/STATUS.md`（`progress-tracker`） |
| 单次开发的完整记录 | `.document/developer/output/`（`dev-output`） |
| 全项目生效的硬约定 | 项目根 / 子项目 `AGENTS.md`（memory 升级而来） |

> memory 中被反复引用的强约束，应择机"毕业"进 AGENTS.md 或 reviewer skill——那里的执行力更强。
