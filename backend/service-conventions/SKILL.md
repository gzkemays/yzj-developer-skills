---
name: service-conventions
description: Service 层开发规范。当需要编写 Service 方法（命名规约）、确定单表操作与跨业务操作的边界、编写 QueryChain 查询构造链、使用 TableDefCollect、确定 Mapper XML 使用场景时使用此 skill。
---

# Service 层开发规范

---

## 一、方法命名规约

| 操作类型 | 命名规则 | 示例 |
|----------|----------|------|
| 获取单个 | `get` 前缀 | `getDtoById()` |
| 获取多个 | `getxxxList` 前缀 | `getDtoListByQuery()` |
| 获取统计值 | `statistics` 前缀 | `statisticsUserCount()` |
| 插入 | `add` 前缀 | `add(AddUserOperate operate)` |
| 删除 | `remove` 前缀 | `removeById()` |
| 修改 | `update` 前缀 | `update(UpdateUserOperate operate)` |

> 如果中间是与当前业务域的 service 命名一致，则可以省略。如 `UserService.getDtoListByQuery()` 而非 `getUserDtoListByQuery()`。

### Service 接口示例

```java
public interface UserService extends IService<UserEntity> {
    /** 新增用户 */
    void add(AddUserOperate operate);

    /** 更新用户 */
    void update(UpdateUserOperate operate);

    /** 删除用户（需要发送审核通知） */
    void removeById(RemoveUserOperate operate);

    /** 根据 ID 获取用户数据模型 */
    UserDTO getDtoById(Long id);

    /** 根据查询条件获取用户数据模型列表 */
    List<UserDTO> getDtoListByQuery(UserInfoQuery query);

    /** 根据查询条件获取用户数据模型分页 */
    Page<UserDTO> getDtoPageByQuery(UserInfoQuery query);
}
```

### 分页查询链路

分页查询涉及两个 Page 类和一个 CommonPage 类，各在不同层使用：

| 类 | 全限定名 | 使用层 | 说明 |
|----|----------|--------|------|
| `Page<T>` | `com.mybatisflex.core.paginate.Page` | **Service 层** | MyBatis-Flex 分页对象，由 `IQueryChain.pageAs()` 返回 |
| `CommonPage<T>` | `com.yeziji.common.model.CommonPage` | **Controller 层** | 框架统一分页响应包装，由 `CommonResult.successPage(page)` 自动转换 |

> **禁止**自行创建 Page 类。始终使用 `com.mybatisflex.core.paginate.Page` 和 `com.yeziji.common.model.CommonPage`。

**Service 层** — 返回 `Page<T>`：

```java
@Override
public Page<ElectronReleaseVersionInfo> getPage(ElectronReleaseVersionInfoQuery query) {
    return ApplicationElectronQueryChain.getElectronReleaseVersionQueryChain(query)
            .orderBy(ApplicationElectronVersionEntity::getIsLatest).desc()
            .orderBy(ApplicationElectronVersionEntity::getCreateTime).desc()
            .pageAs();
}
```

**Controller 层** — 用 `CommonResult.successPage()` 包装：

```java
@PostMapping("/page")
public CommonResult<CommonPage<ApplicationVersion>> getPage(@RequestBody ApplicationVersionQuery query) {
    return CommonResult.successPage(applicationVersionService.getPage(query));
}
```

---

## 二、职责边界

### 核心原则

| 操作类型 | Service 层规范 | 说明 |
|----------|----------------|------|
| 单表写操作（增/删/改） | ✅ 允许 | `add()`, `update()`, `removeById()` |
| 单表查询操作 | ✅ 允许 | `getById()`, `getListByQuery()` |
| 跨业务/跨表写操作 | ❌ 禁止 | 应在 integration 层 Flow 中处理 |
| 跨业务/跨表查询 | ⚠️ 通过 QueryChain 允许 | 仅限 SQL 层面的连表查询 |

### 正确：单表操作

```java
public class UserServiceImpl implements UserService {
    @Resource
    private UserMapper userMapper;

    @Override
    public void add(AddUserOperate operate) {
        UserEntity existUser = userMapper.selectOne(
            UserEntity::getUsername, operate.getUsername()
        );
        if (existUser != null) {
            throw new BusinessException("用户名已存在");
        }
        UserEntity entity = UserConvertAid.convertToEntity(operate);
        userMapper.insert(entity);
    }
}
```

### 错误：Service 中跨业务写操作

```java
// ❌ 禁止在 UserService 中操作 AccountService、OrderService
public class UserServiceImpl implements UserService {
    @Resource
    private AccountService accountService;  // 禁止引入
    @Resource
    private OrderService orderService;      // 禁止引入

    @Override
    public void register(UserRegisterOperate operate) {
        userMapper.insert(entity);
        accountService.createAccount(operate.getUserId());  // 应在 Flow 中
        orderService.createInitOrder(operate.getUserId());  // 应在 Flow 中
    }
}
```

### 错误：Service 中直接操作其他表 Mapper

```java
// ❌ 禁止在 OrderService 中直接操作 OrderItemMapper
public class OrderServiceImpl implements OrderService {
    @Resource
    private OrderItemMapper orderItemMapper;  // 禁止直接操作其他表的 Mapper

    @Override
    public void add(OrderAddOperate operate) {
        orderMapper.insert(order);
        orderItemMapper.insert(itemEntity);  // 应通过 OrderItemService 处理
    }
}
```

---

## 三、QueryChain 查询构造链

### 包结构与命名

```
domain/{业务域}/
└── mapper/
    └── queryChain/
        └── {业务名}QueryChain.java
```

### TableDef 统一引用

通过 `TableDefCollect` 类统一引用所有 TableDef：

```java
import static com.yeziji.{project}.support.TableDefCollect.*;
```

### QueryChain 实现示例

```java
package com.yeziji.{project}.domain.{业务域}.mapper.queryChain;

import com.mybatisflex.core.query.If;
import com.yeziji.mybatis.IQueryChain;

import static com.yeziji.{project}.support.TableDefCollect.*;

/**
 * {业务描述}查询构造链
 *
 * @author hwy
 * @since 2026/03/21
 **/
public class CustomerInfoQueryChain {

    public static IQueryChain<CustomerInfoDTO, CustomerInfoEntity> getDtoQueryChain(CustomerInfoQuery query) {
        return getDtoQueryChainBase(query)
                .select(CUSTOMER_INFO.DEFAULT_COLUMNS)
                .leftJoin(MerchantEntity.class)
                .on(queryWrapper ->
                        queryWrapper.where(MerchantEntity::getId).eq(CustomerInfoEntity::getMerchantId)
                )
                .defaultOrderDescBy(CustomerInfoEntity::getCreateTime);
    }

    private static IQueryChain<CustomerInfoDTO, CustomerInfoEntity> getDtoQueryChainBase(CustomerInfoQuery query) {
        return IQueryChain.of(query, CustomerInfoEntity.class)
                .commonWrappers(CustomerInfoEntity::getName, CustomerInfoEntity::getAbbreviation)
                .where(CustomerInfoEntity::getStatus).eq(query.getStatus(), If::notNull)
                .and(CustomerInfoEntity::getRemark).like(query.getRemark(), If::notNull);
    }
}
```

### QueryChain 常用方法

| 方法 | 说明 |
|------|------|
| `IQueryChain.of(query, Entity.class)` | 创建查询链 |
| `.select(TableDef.DEFAULT_COLUMNS)` | 选择默认列 |
| `.leftJoin(Entity.class)` | 左连接 |
| `.on(queryWrapper -> ...)` | 连接条件 |
| `.where(...).eq(value, If::notNull)` | 条件成立才拼接 |
| `.commonWrappers(...fields)` | 通用模糊查询 |
| `.defaultOrderDescBy(...)` | 默认降序排序 |

---

## 四、Mapper 使用规则

| 场景 | 方式 |
|------|------|
| 单表/简单跨表查询 | **QueryChain**（首选） |
| 复杂多表关联、动态 SQL、批量操作 | **Mapper XML** |

> QueryChain 为首选，XML 仅用于 QueryChain 无法表达的复杂 SQL。

---

## 五、IService 的 queryChain() 使用

Service 继承 `IService<Entity>` 后可直接调用 `queryChain()` 进行简单查询，无需定义独立的 QueryChain 类：

```java
// 在 Flow 或 ServiceImpl 中直接使用
UserEntity user = userService.queryChain()
        .where(UserEntity::getUsername).eq(username)
        .oneOpt().orElseThrow(() -> new ApiException(ErrorMsg.USER_NOT_FOUND));
```

> 适用于简单的单条件查询。复杂查询应抽取为独立的 QueryChain 类。
