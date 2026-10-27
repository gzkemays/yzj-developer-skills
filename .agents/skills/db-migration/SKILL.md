---
name: db-migration
description: "生成 SQL 数据库迁移脚本。在后端仓库 src/main/resources/db/migration/ 下生成带时间戳的 成对 SQL（up + down），并关联 .document/plan/ 中对应的迭代文档。 仅在用户通过 /db-migration 显式调用时执行。 disable-model-invocation: true"
---

# Database Migration Generator

> 适用于未集成 Flyway / Liquibase、但需要可审计 SQL 变更历史的项目。本 skill 约定统一的
> 迁移文件结构，未来接入 Flyway 可直接迁移。已集成迁移框架的项目按框架规范执行，仅参考本文的设计规则。

---

## 调用方式

```
/db-migration <动作描述>
```

例：
```
/db-migration 给 system_user 表加 last_login_at 列
/db-migration 新建 work_item 表
/db-migration 给 organization_member 表加复合索引
```

---

## 工作流

### 步骤 1 — 收集信息

询问用户（如未在调用中提供）：

1. **影响哪些表**？（必填）
2. **所属迭代**？（关联 `.document/plan/` 下哪份文档）
3. **是否破坏性变更**？（DROP COLUMN / DROP TABLE / 改列类型）—— 需警告并要求显式确认
4. **是否多租户表**？（是否需要 `organization_id` 字段 + 索引）

### 步骤 2 — 检查目录与现有迁移

```bash
ls {backend}/src/main/resources/db/migration/
```

目录不存在则创建并告知用户；检查同表已有迁移避免冲突。

### 步骤 3 — 文件命名

```
V{yyyyMMddHHmm}__{snake_case_description}.sql       # up
V{yyyyMMddHHmm}__{snake_case_description}.down.sql  # down
```

### 步骤 4 — 文件模板

**up 脚本**：

```sql
-- ============================================================
-- 迁移：{描述}
-- 关联迭代：.document/plan/{xx-xxx.md}
-- 生成时间：{ISO datetime}
-- 破坏性变更：是 / 否
-- ============================================================

ALTER TABLE system_user
    ADD COLUMN last_login_at DATETIME NULL COMMENT '最后登录时间' AFTER update_time;

CREATE INDEX idx_system_user_last_login_at ON system_user (last_login_at);
```

**down 脚本**：

```sql
-- ============================================================
-- 回滚：{描述}
-- 注意：执行前确认无数据依赖该字段
-- ============================================================

DROP INDEX idx_system_user_last_login_at ON system_user;

ALTER TABLE system_user
    DROP COLUMN last_login_at;
```

### 步骤 5 — 多租户表约定

业务数据表需要租户隔离时，必须包含：

```sql
CREATE TABLE work_item (
    id              BIGINT       NOT NULL AUTO_INCREMENT,
    organization_id BIGINT       NOT NULL COMMENT '组织 ID（多租户隔离）',
    -- 业务字段...
    create_time     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    create_user_id  BIGINT       NULL,
    update_user_id  BIGINT       NULL,
    deleted         TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    PRIMARY KEY (id),
    KEY idx_organization_id (organization_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT '工作项';
```

**强制规则**：

- [ ] 所有业务表必须有 `organization_id` + 索引（多租户项目；字段名禁止 `org_id` 简写）
- [ ] 所有表必须有 `create_time` / `update_time` / `deleted`（与 CommonEntity 公共字段对齐）
- [ ] 字符集统一 `utf8mb4`；引擎统一 `InnoDB`；字段必须有 `COMMENT`
- [ ] 新建/变更表后同步维护 TableDef（`tabledef` skill）与 Entity

### 步骤 6 — 验收清单

```markdown
## ✅ 迁移脚本已生成

| 文件 | 路径 |
|------|------|
| up | {backend}/src/main/resources/db/migration/V{timestamp}__{name}.sql |
| down | 同上 .down.sql |

**关联迭代**：.document/plan/{xx-xxx.md}

**下一步**：
1. 检查 SQL 是否符合预期
2. 本地数据库执行 up 脚本
3. 验证 down 脚本可正常回滚（推荐）
4. 同步维护 Entity + TableDef，提交时关联迭代 commit
```

---

## 破坏性变更规则

变更包含 `DROP TABLE` / `DROP COLUMN` / `MODIFY COLUMN` 改类型 / `RENAME` 之一时，**必须**：

1. 红色警告 + 列出潜在影响
2. 要求用户回答："是否已确认无业务代码依赖该字段/表？"
3. 用户明确确认后才生成脚本
4. SQL 顶部添加 `-- ⚠️ 破坏性变更` 标记

---

## 字段命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 主键 | `id`（BIGINT AUTO_INCREMENT 或雪花 ID，按项目约定） | — |
| 外键 | `{表名单数}_id` | `user_id`, `organization_id` |
| 时间 | snake_case + `_time` 或 `_at` | `create_time`, `last_login_at` |
| 布尔 | `is_xxx` 或 `enabled` / `deleted`；**注意**：列名可用 `is_xxx`，但 Java 字段名禁止 is 前缀，用 `xxxFlag` + `@Column("is_xxx")` 映射 | `is_default` ↔ `defaultFlag` |
| 枚举 | 字符串或 TINYINT（优先字符串便于调试） | — |
| 索引 | `idx_{table}_{cols}` | `idx_work_item_organization_id_status` |
| 唯一 | `uk_{table}_{cols}`；**软删除表**注意唯一键与逻辑删除的 re-insert 冲突（add 应实现 restore-or-insert） | `uk_system_user_username` |
