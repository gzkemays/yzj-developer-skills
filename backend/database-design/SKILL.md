---
name: database-design
description: YZJ 后端数据库设计建议指南（非强制 DDL 模板）。当需要在开发任务中规划新表 / 新字段 / 索引设计、与开发者讨论数据模型方案、评估字段类型选择、判断是否需要扩展现有表 vs 新建表时使用此 skill。**注意**：本 skill 只产出"建议"和"讨论材料"，不直接生成 DDL 或 Entity；最终 DDL 落地与 Entity / TableDef 生成由开发者通过项目代码生成器完成。
---

# YZJ 后端数据库设计建议

> **本 skill 是"建议器"，不是"执行器"**。Agent 在与开发者讨论方案时，提供数据模型建议；**禁止**自动生成 DDL 文件或手动编写 `entity/table/` 下的 TableDef。最终落地由开发者：
> 1. 自行确认 DDL
> 2. 通过 YZJ 成熟的代码生成器生成 Entity + Mapper + TableDef
>
> 本文档侧重"设计原则"和"讨论维度"，不提供固定模板。

---

## 一、使用方式

Agent 在以下场景被触发：

| 场景 | Agent 行为 |
|------|-----------|
| 开发者描述新功能涉及新数据 | 主动分析需求，给出建议表结构与字段类型 |
| 开发者询问"这字段加在哪个表" | 评估扩展现有表 vs 新建表的 trade-off |
| 开发者询问"加什么索引" | 基于查询场景给出索引建议 |
| 开发者确认 DDL 方案 | **停止**，提示开发者通过代码生成器执行 |

**禁止**：
- 直接写 SQL DDL 文件到项目
- 手动创建 / 修改 `domain/{业务}/entity/table/` 下的任何文件（这是代码生成器的产出）
- 跳过开发者确认，直接生成 Entity 类

---

## 二、设计讨论维度（Checklist）

与开发者讨论数据模型时，逐项覆盖以下维度：

### 2.1 表归属

- 属于哪个业务域？（决定 `domain/{业务}/entity/` 放置位置）
- 是扩展现有表还是新建表？判断标准：
  - 是同一业务实体的属性 → 扩展现有表
  - 是独立业务实体或会被独立查询 → 新建表
  - 是 1:N 的子集 → 新建子表
- 是否会被多个业务域共享？如果是，是否需要在 common 层放置定义？

### 2.2 字段设计

| 维度 | 讨论点 |
|------|--------|
| 字段命名 | 与业务一致，避免歧义；snake_case |
| 字段类型 | 整数选 `INT` / `BIGINT`；金额必须 `DECIMAL(precision, scale)`，禁止 `FLOAT/DOUBLE`；时间统一 `DATETIME` 或 `BIGINT`（时间戳） |
| 字符串长度 | VARCHAR 必须明确长度上限，避免 `TEXT` 兜底 |
| 可空性 | 业务必填字段 `NOT NULL` + 合理默认值；可空字段允许 `NULL` |
| 是否加密 | 敏感字段（手机号、身份证、银行卡）讨论是否使用 `@Encryption` 注解 |
| 枚举字段 | 是否对应已有 `CommonEnum`；约定整数 code 还是字符串 |

### 2.3 CommonEntity 公共字段

所有业务表继承 `CommonEntity`，框架已自动管理以下字段（**不要在 DDL 中遗漏**）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT | 主键（雪花算法或自定义生成） |
| `create_time` | DATETIME | 创建时间，框架 `DefaultOnInsertListener` 自动填充 |
| `update_time` | DATETIME | 更新时间，框架 `DefaultOnUpdateListener` 自动填充 |
| `create_by` | BIGINT | 创建人 ID |
| `update_by` | BIGINT | 更新人 ID |

> 具体字段以项目实际 CommonEntity 定义为准，讨论时确认与项目一致。

### 2.4 索引设计

讨论维度：
- **查询场景**：常用的 WHERE / ORDER BY / GROUP BY 字段
- **唯一性约束**：业务唯一的字段（如 `username`、`order_no`）需要唯一索引
- **复合索引顺序**：高频查询字段在前，遵循最左前缀原则
- **避免冗余索引**：单字段索引被复合索引最左前缀覆盖时可省略
- **JSON 字段**：仅记录型数据用，业务查询字段不要用 JSON 列

**索引命名建议**（与项目现有命名风格一致即可）：
- 普通索引：`idx_{表名简写}_{字段简写}`
- 唯一索引：`uk_{表名简写}_{字段简写}`

### 2.5 软删除

- YZJ 默认是否启用软删？询问开发者
- 启用时统一 `deleted` 字段（SMALLINT 或 TINYINT，0=未删 1=已删）
- 软删后唯一索引需考虑：`UNIQUE (xxx) WHERE deleted = 0` 或 `UNIQUE (xxx, deleted)`

### 2.6 扩展性

- 是否预留多租户字段 `tenant_id`？
- 是否需要 `version` 字段做乐观锁？
- 是否需要 `remark` / `extra_json` 兜底字段（适度使用）？

---

## 三、建议输出格式

Agent 在讨论时给出的建议应包含以下结构，方便开发者评审：

```markdown
## 数据设计建议：{业务功能}

### 涉及的表
- 新建表：[表名]，理由：[为什么新建而非扩展]
- 扩展表：[表名]，新增字段：[字段列表]

### 推荐表结构（讨论用，非最终 DDL）

| 字段 | 类型 | 可空 | 索引 | 说明 |
|------|------|:----:|------|------|
| id | BIGINT | NO | PK | CommonEntity 提供 |
| xxx | VARCHAR(64) | NO | uk_xxx | 业务唯一标识 |
| ... | ... | ... | ... | ... |

### 索引建议
1. `uk_{表}_{字段}`：业务唯一，理由：[查询/约束场景]
2. `idx_{表}_{字段}`：高频查询，理由：[场景]

### 待开发者确认的点
- [ ] 是否启用软删？
- [ ] {字段} 是否需要加密（@Encryption）？
- [ ] {字段} 字符串长度上限多少合适？

### 下一步
请确认上述设计后，使用项目代码生成器生成 Entity / Mapper / TableDef。
**本 skill 不会自动生成 DDL 或 Entity 文件。**
```

---

## 四、典型决策示例

### 4.1 扩展现有表 vs 新建表

**场景**：用户需要绑定多个手机号

```
讨论：
- 一个 user 对应多个 phone → 1:N 关系
- phone 会被独立查询（如"按手机号查用户"）
- 结论：新建 user_phone 表，外键 user_id

✓ 建议：新建 user_phone 表
✗ 不建议：在 user 表上加 phone2, phone3 字段
```

### 4.2 金额字段类型选择

```
场景：订单金额、账户余额
- ✗ FLOAT / DOUBLE → 精度丢失
- ✓ DECIMAL(19, 4) → 业务推荐精度（按项目实际确定）
- 业务代码使用 BigDecimal 处理
```

### 4.3 时间字段类型选择

```
场景：CommonEntity 自动管理时间 → DATETIME（与项目一致）
场景：业务时间戳（如订单截止时间）→ DATETIME 或 BIGINT（毫秒）
原则：与同业务域现有字段类型保持一致
```

---

## 五、与代码生成器的协作流程

```
1. Agent 与开发者讨论数据设计
        ↓
2. Agent 输出"设计建议文档"（如本文第三节格式）
        ↓
3. 开发者评审 → 调整 → 确认
        ↓
4. 开发者自行执行 DDL（数据库迁移工具或手动 SQL）
        ↓
5. 开发者运行 YZJ 代码生成器，生成：
   - domain/{业务}/entity/{业务}Entity.java
   - domain/{业务}/entity/table/{业务}TableDef.java（自动）
   - domain/{业务}/mapper/{业务}Mapper.java
        ↓
6. 开发者将生成的 TableDef 注册到 support/TableDefCollect.java
        ↓
7. Agent 继续业务代码开发（Service / Controller / Flow）
```

---

## 六、禁止事项

1. 直接生成 / 修改 `domain/{业务}/entity/table/` 下的 TableDef 文件（代码生成器的产物）
2. 直接写 SQL DDL 文件到项目（DDL 落地由开发者自行执行）
3. 跳过与开发者的确认，自动落地数据模型
4. 在建议中使用 `FLOAT` / `DOUBLE` 表示金额
5. 在建议中使用无长度限制的 `TEXT` / `LONGTEXT` 替代合理 `VARCHAR(n)`
6. 在建议中省略 CommonEntity 已提供的公共字段说明（避免开发者重复添加）
