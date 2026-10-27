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
> 域名词与 Service 不同名时**保留**：`OrgService.getDepartmentDtoListByOrgId()`——Org ≠ Department，省掉就看不出返回的是什么。

### 分层适用边界（别一把尺子量到底）

| 层 | 是否套用本规约 | 说明 |
|----|:---:|------|
| **Service 接口 / 实现** | ✅ 强制 | 本规约的主战场 |
| **Mapper 接口** | ❌ 用 MyBatis 惯例 | `get` → `select`，其余结构一致：`selectByQuery` / `selectListByIds`；写操作 `insert` / `update` / `batchInsert` / `markDeletedByIds` |
| **Controller** | ❌ 镜像端点路径 | `/v1/admin/user/page` → `page()`、`/info` → `info()`——Controller 是路由壳，方法名与 URL 对得上比套规约更有价值 |
| **SDK / gRPC 客户端接口** | ✅ 套用，但**保留域名词** | 跨服务语境下省略域名词会失去可读性：`userClient.getUserDtoById()` 而非 `getDtoById()` |
| **ConvertAid / 工具类** | ◯ 尽量对齐 | 取数方法 `get` 前缀；`convertToXxx` / `buildXxx` 等既有转换惯例保留 |

**动作型方法不在规约覆盖范围**：触发同步、撤销令牌、发起授权、刷新缓存这类**非 CRUD 动作**（`pullDepartments()` / `revoke()` / `authorize()` / `refreshExpiringTokens()`）用能说清动作的动词即可，不要硬套 `get` / `add` / `update`。

### 存量代码的处理

**新代码强制遵循；存量不做一次性全仓重命名。**

- 改动某个方法时**顺手改名**可以，但要确认调用方全部跟上（Service 接口不是 HTTP 契约，改名不影响前端 / SDK 消费方，风险可控）
- **成规模的统一**单独立迭代、按业务域分批，**不混进特性分支**——纯重命名的大 diff 会淹掉真正要 review 的逻辑
- backend-reviewer 对存量不合规方法名只报 🟢 提示，对新增方法报 🟡 警告

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

### 分页转换流程图

```
┌─────────────────┐   pageAs()    ┌─────────────────────────┐
│  QueryChain     │ ────────────► │  Page<T>                │
│  (mybatis-flex) │               │  com.mybatisflex...Page │
└─────────────────┘               └──────────┬──────────────┘
                                             │ Service 层返回 Page<T>
                                             ▼
                                  ┌─────────────────────────┐
                                  │  Controller 层          │
                                  │  CommonResult.successPage(page) │
                                  └──────────┬──────────────┘
                                             │ 自动转 CommonPage<T>
                                             ▼
                                  ┌─────────────────────────┐
                                  │  CommonResult<CommonPage<T>> │
                                  │  返回前端                │
                                  └─────────────────────────┘
```

**关键节点**：
- Service 层只与 `Page<T>` 打交道，不感知 `CommonPage`
- Controller 层用 `CommonResult.successPage(page)` 完成转换，**禁止**手动 `new CommonPage<>(...)`
- 业务代码任何位置都不应该 `import com.yeziji.common.model.CommonPage` 单独构造，统一走 `CommonResult.successPage()`

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
