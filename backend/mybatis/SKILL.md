---
name: mybatis
description: yzj-mybatis 数据库查询构建指南。当需要使用 IQueryChain 流式查询 API、CommonQuery DTO、范围查询（TimeRange/NumberRange/BigDecimalRange）、分页排序、关键字搜索、数据加解密（@Encryption）、公共字段自动填充时使用此 skill。
---

# yzj-mybatis 数据库查询构建

---

## 一、IQueryChain 流式 API

`IQueryChain<T, E>` 是基于 MyBatis-Flex `QueryChain` 的增强查询构建器，配合 `CommonQuery<T>` DTO 自动处理分页、排序、关键字搜索和范围过滤。`T` 为返回的 DTO 类型，`E` 为实体类。

### 标准查询模式

```java
// 1. 查询 DTO（继承 CommonQuery，泛型指定返回的 DTO）
@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = true)
public class UserQuery extends CommonQuery<UserDTO> {
    @JsonDeserialize(using = NumberRange.NumberRangeDeserializer.class)
    private NumberRange ageRange;
}

// 2. Service 层
public Page<UserDTO> getDtoPageByQuery(UserQuery query) {
    return IQueryChain.of(query, User.class)     // query 在前，实体类在后
            .commonWrappers(USER.NAME)               // = commonWrapper() + keyword LIKE 匹配
            .and(BaseRange.buildQueryCondition(query.getAgeRange(), USER.AGE))
            .defaultOrderDescBy(USER.CREATE_TIME)    // 无客户端排序时的默认排序
            .pageAs();                               // 分页 + 自动转 DTO
}
```

### 工厂方法

| 方法 | 说明 |
|------|------|
| `IQueryChain.of(query, Entity.class)` | 有 CommonQuery 时用（**query 在前**） |
| `IQueryChain.of(Entity.class)` | 无 CommonQuery 时用 |

---

## 二、commonWrapper vs commonWrappers

| 方法 | 等价于 | 何时用 |
|------|--------|--------|
| `commonWrapper()` | 处理 id/ids/时间范围 | 不需要关键字搜索 |
| `commonWrappers(cols...)` | `commonWrapper()` + `commonKeywords(cols...)` | 需要关键字搜索（两者内部已去重，不要同时调用） |
| `commonOrKeywords(cols...)` | keyword 在多列间用 OR 匹配 | 跨列 OR 搜索 |

`commonWrapper()` 自动处理：`ids`（合并 `id` 和 `ids`）、`createTimeRange`、`updateTimeRange`。

---

## 三、CommonQuery 关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `keyword` | String | 由 `commonWrappers(cols...)` 消费，做 LIKE 匹配 |
| `id` / `ids` | Long / Collection\<Long\> | `getIds()` 统一获取（已合并） |
| `createTimeRange` | TimeRange | `commonWrapper()` 自动处理 |
| `updateTimeRange` | TimeRange | `commonWrapper()` 自动处理 |
| `orderBy` | List\<OrderBy\> | `commonOrderBy()` 消费，支持驼峰/下划线自动转换 |
| `page` | IPage\<T\> | `pageAs()` 内部调用 `ifPresentDefaultPage()`，null 时默认第1页10条 |

---

## 四、范围查询

```java
// 实例方法（推荐，null 时跳过 and()）
if (query.getAgeRange() != null) {
    chain.and(query.getAgeRange().buildQueryCondition(USER.AGE));
}

// 静态方法（null-safe，range 为 null 时返回空条件）
chain.and(BaseRange.buildQueryCondition(query.getAgeRange(), USER.AGE));

// 直接值（不使用 Range 对象）
chain.and(ConditionAid.between(USER.AGE, 18, 60));  // 任一边界为 null 则自动降级为 >= 或 <=
```

---

## 五、终端操作

| 方法 | 说明 |
|------|------|
| `pageAs()` | 分页查询 → T（用 queryClass 自动转换） |
| `listAs()` | 列表查询 → List\<T\> |
| `oneAs()` | 单对象查询 → T |
| `oneAsOpt()` | 单对象查询 → Optional\<T\> |
| `defaultOrderDescBy(cols...)` | 默认降序（客户端有 orderBy 时被 commonOrderBy 取代） |
| `defaultOrderAscBy(cols...)` | 默认升序 |

---

## 六、数据加解密

### @Encryption 注解

```java
public class UserEntity {
    @TableField("phone")
    private String phone;

    @Encryption
    @TableField("id_card")
    private String idCard;
}
```

支持策略：
- `EncryptionStrategyEnum.AES`: AES 加密
- `EncryptionStrategyEnum.RSA`: RSA 加密

---

## 七、公共字段自动填充

框架通过 `DefaultOnInsertListener` 和 `DefaultOnUpdateListener` 自动处理创建时间、更新时间等公共字段，无需手动赋值。

---

## 八、常见错误

| 错误 | 正确做法 |
|------|---------|
| `IQueryChain.of(User.class, query)` 参数顺序反了 | `IQueryChain.of(query, User.class)`（query 在前） |
| 同时调用 `commonWrapper()` 和 `commonWrappers()` | `commonWrappers()` 内部已调用 `commonWrapper()`，只用其一 |
| `ConditionAid.between(col, range)` 传 Range 对象 | Range 对象用 `range.buildQueryCondition(col)` |
| 分别处理 `id` 和 `ids` | 用 `query.getIds()` 统一获取 |
| `CommonQuery` 直接实例化获取 queryClass | 必须**继承** CommonQuery 才能通过反射获取泛型 |
