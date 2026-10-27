---
name: tabledef
description: "MyBatis-Flex TableDef 手写维护规范。适用于禁用 mybatis-flex APT 编译器自动生成、 由项目手动维护 TableDef 的项目。当新增实体类（Entity）、修改实体字段、或创建新业务域时， 必须同步创建或更新对应的 TableDef。即使用户没有明确提到 TableDef，只要涉及实体类的 新增或字段变更，都应主动执行此 SKILL。"
---

# MyBatis-Flex TableDef 手写维护规范

> 适用前提：项目已禁用 mybatis-flex APT（`mybatis-flex.config` 中 `processor.enable=false`），
> 所有 TableDef 在 `src/main/java` 中手动维护，不依赖编译器自动生成。
> 若项目仍使用 APT 自动生成，则本 skill 不适用（生成物禁止手改）。

---

## 一、触发时机

| 场景 | 操作 |
|------|------|
| 新建 Entity 类 | 创建对应的 TableDef |
| Entity 新增字段 | 在 TableDef 中追加 QueryColumn + 更新 DEFAULT_COLUMNS |
| Entity 删除字段 | 在 TableDef 中移除 QueryColumn + 更新 DEFAULT_COLUMNS |
| Entity 修改 `@Column` 映射 | 更新 QueryColumn 的 column name 参数 |
| Entity 修改 `@Table` 名称 | 更新 TableDef 构造函数和 `as()` 中的 table name |
| 新建业务域 | 创建 `domain/{业务}/entity/table/` 包 |

---

## 二、文件位置与命名

```
domain/{业务}/entity/table/{ClassName}TableDef.java
```

- 类名 = 实体类名 + `TableDef`（如 `WorkItemEntity` → `WorkItemEntityTableDef`）
- 静态实例名 = 表名大写 + `_ENTITY`（如 `WORK_ITEM_ENTITY`）
- 项目历史遗留的不带 `Entity` 后缀命名（如 `UserTableDef`）以项目现状为准；**新业务域统一带 `Entity`**

---

## 三、代码模板

### 3.1 CommonEntity 子类（全局表）

```java
package com.yeziji.{project}.domain.{业务}.entity.table;

import com.mybatisflex.core.query.QueryColumn;
import com.mybatisflex.core.table.TableDef;

import java.io.Serial;

/**
 * {中文表名} 表定义层。
 *
 * @author {author}
 * @since {date}
 */
public class XxxEntityTableDef extends TableDef {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * {中文表名}
     */
    public static final XxxEntityTableDef XXX_ENTITY = new XxxEntityTableDef();

    // ── 主键 ──

    /**
     * 自增 id
     */
    public final QueryColumn ID = new QueryColumn(this, "id");

    // ── 业务字段（按逻辑顺序排列，每个字段附 Javadoc） ──

    // ...

    // ── CommonEntity 公共字段 ──

    /**
     * 创建时间
     */
    public final QueryColumn CREATE_TIME = new QueryColumn(this, "create_time");

    /**
     * 创建用户 ID
     */
    public final QueryColumn CREATE_USER_ID = new QueryColumn(this, "create_user_id");

    /**
     * 更新时间
     */
    public final QueryColumn UPDATE_TIME = new QueryColumn(this, "update_time");

    /**
     * 更新用户 ID
     */
    public final QueryColumn UPDATE_USER_ID = new QueryColumn(this, "update_user_id");

    /**
     * 删除标识
     */
    public final QueryColumn DELETED = new QueryColumn(this, "deleted");

    // ── 元字段 ──

    /**
     * 所有字段。
     */
    public final QueryColumn ALL_COLUMNS = new QueryColumn(this, "*");

    /**
     * 默认字段，不包含逻辑删除或者 large 等字段。
     */
    public final QueryColumn[] DEFAULT_COLUMNS = new QueryColumn[]{ID, /* 业务字段... */ CREATE_TIME, CREATE_USER_ID, UPDATE_TIME, UPDATE_USER_ID, DELETED};

    public XxxEntityTableDef() {
        super("", "table_name");
    }

    private XxxEntityTableDef(String schema, String name, String alisa) {
        super(schema, name, alisa);
    }

    @Override
    public XxxEntityTableDef as(String alias) {
        String key = getNameWithSchema() + "." + alias;
        return getCache(key, k -> new XxxEntityTableDef("", "table_name", alias));
    }
}
```

### 3.2 CommonBusinessEntity 子类（多租户业务表）

与 CommonEntity 模板相同，区别在于**业务字段区域**末尾追加多租户字段，且 `DEFAULT_COLUMNS` 中包含它：

```java
    // ── 多租户字段 ──

    /**
     * 所属组织 ID（多租户隔离）
     */
    public final QueryColumn ORGANIZATION_ID = new QueryColumn(this, "organization_id");
```

---

## 四、字段映射规则

### 4.1 Java 字段名 → QueryColumn 常量名

| Java 字段 | QueryColumn 常量 | column 参数 |
|-----------|-----------------|-------------|
| `projectId` | `PROJECT_ID` | `"project_id"` |
| `itemKey` | `ITEM_KEY` | `"item_key"` |

规则：camelCase → UPPER_SNAKE_CASE，column 参数 = 数据库列名（snake_case）。

### 4.2 特殊 `@Column` 映射

实体字段使用 `@Column(value = "xxx")` 自定义列名时，QueryColumn 的 column 参数必须使用 `@Column` 中的值：

```java
// Entity 中：
@Column("is_default")
private Boolean defaultFlag;

// TableDef 中：
public final QueryColumn DEFAULT_FLAG = new QueryColumn(this, "is_default");
```

**常量名跟随 Java 字段名**（`DEFAULT_FLAG`），**column 参数跟随 `@Column` 注解**（`"is_default"`）。

### 4.3 不纳入 TableDef 的字段

| 情况 | 说明 |
|------|------|
| `@Column(ignore = true)` | 不生成 QueryColumn |
| `transient` 字段 | 非持久化字段不生成 |
| 仅存在于 VO/DTO 的字段 | TableDef 只反映数据库列 |

---

## 五、注册到 TableDefCollect

新建 TableDef 后，必须在 `support/TableDefCollect.java` 中注册：

```java
// ==================== {业务域}相关 ====================

/**
 * {中文表名}
 */
public static final XxxEntityTableDef XXX = XxxEntityTableDef.XXX_ENTITY;
```

**常量命名**：TableDefCollect 中的常量名是**简短形式**（不带 `_ENTITY` 后缀），如 `WORK_ITEM`、`PROJECT_MEMBER`。
业务代码一律通过 `TableDefCollect.XXX` 引用，**禁止局部变量持有 TableDef 或直接引用 `XxxEntityTableDef.XXX_ENTITY`**。

---

## 六、字段排列顺序

```
ID                          ← 主键（固定第一）
{业务字段}                   ← 按逻辑分组排列
ORGANIZATION_ID             ← 多租户字段（仅 CommonBusinessEntity）
CREATE_TIME / CREATE_USER_ID / UPDATE_TIME / UPDATE_USER_ID / DELETED   ← 公共字段
ALL_COLUMNS / DEFAULT_COLUMNS   ← 元字段
```

`DEFAULT_COLUMNS` 数组的元素顺序与字段声明顺序一致。

---

## 七、Javadoc 规范

- 每个 QueryColumn 字段**必须**有 Javadoc，至少一句话说明含义
- 枚举类型字段使用 `@see` 指向枚举类
- 反直觉设计必须标注（遵循 backend-reviewer Doc 精简原则）：

```java
/**
 * 反直觉点：字段名 {@code status} 但实际是 workflow_node 表的外键 ID。
 * 状态由配置驱动，而非硬编码枚举。
 */
public final QueryColumn STATUS = new QueryColumn(this, "status");
```

---

## 八、与大字段（isLarge）的配合

`@Column(isLarge = true)` 标记的字段（LONGTEXT 等）**不进 DEFAULT_COLUMNS**；
需要读取大字段处必须 `selectOneByQuery(QueryWrapper.create().select(TableDefCollect.XXX.ALL_COLUMNS)...)`，
`queryChain().one()` / `getById()` 默认不返回大字段——这是 backend-reviewer Step 3 的必查项。

---

## 九、常见错误

| 错误 | 正确做法 |
|------|----------|
| column 参数写 Java 字段名（`"projectId"`） | 写数据库列名（`"project_id"`） |
| 漏掉 `@Serial` + `serialVersionUID` | 每个 TableDef 类都要加 |
| `DEFAULT_COLUMNS` 漏了 `DELETED` | 手写 TableDef 包含 DELETED |
| `as()` 方法返回父类 `TableDef` | 返回具体类型 `XxxEntityTableDef` |
| 忘记注册到 `TableDefCollect` | 新建后必须注册（backend-reviewer 禁止 #10 🔴） |
| 新增字段后未更新 `DEFAULT_COLUMNS` | 修改字段时同步更新数组 |
