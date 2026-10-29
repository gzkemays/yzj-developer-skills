---
name: integration-flow
description: Integration 集成层开发规范。当需要编写跨业务 Flow、定时任务 Job、事件监听 Listener、初始化器 Initializer，或者需要判断逻辑应放在 Service 还是 Flow 中时使用此 skill。
---

# Integration 集成层开发规范

---

## 一、层级定位

Integration 层编排跨业务流程，不直接操作数据库，而是调用 `domain` 层的 Service。

```
domain: "读操作跨业务查询、单业务写操作"
integration: "多业务写操作、复杂步骤/流程/事务"
```

---

## 二、包结构

```
integration/
├── jobs/                           # 定时任务
│   └── {描述}Job.java
├── listener/                       # 事件监听器
│   └── {描述}Listener.java
├── initializer/                    # 初始化器
│   └── {描述}Initializer.java
└── business/                       # 业务模块（按业务域细分）
    ├── auth/
    │   └── AuthLoginFlow.java
    ├── db/
    │   └── PlatformClientRegisterCloudDbFlow.java
    └── application/
        └── UpdateApplicationFlow.java
```

---

## 三、Flow — 跨业务编排

### 命名与放置

- 命名格式：`{业务描述}Flow`
- 放置于 `integration/business/{业务域}/`
- 使用 `@Component` 注解

### 编写规范

```java
/**
 * 授权登录流程
 *
 * @author hwy
 * @since 2026/02/18 17:38
 **/
@Slf4j
@Component
@Validated
public class AuthLoginFlow {
    @Resource
    private PasswordEncoder passwordEncoder;
    @Resource
    private IJwtTokenGenerate iJwtTokenGenerate;
    @Resource
    private UserService userService;
    @Resource
    private PlatformClientDatasourceService platformClientDatasourceService;

    /**
     * 密码授权登录
     *
     * <p>如果认证成功则直接为 response 赋值 token 请求头</p>
     */
    public void passwordLogin(HttpServletResponse response, @Valid PasswordAuth passwordAuth) {
        // 1. 查询用户
        UserEntity user = userService.queryChain()
                .where(UserEntity::getUsername).eq(passwordAuth.username())
                .oneOpt().orElseThrow(() -> new ApiException(ErrorMsg.USER_NOT_FOUND));

        // 2. 验证密码
        if (!passwordEncoder.matches(passwordAuth.password(), user.getPassword())) {
            throw new ApiException(ErrorMsg.USER_NOT_FOUND);
        }

        // 3. 生成 Token
        SecurityToken securityToken = iJwtTokenGenerate.generate(
                JwtInfo.builder()
                        .id(user.getId().toString())
                        .authType(SecurityAuthTypeEnum.PASSWORD.toString())
                        .username(user.getUsername())
                        .build()
        );

        // 4. 写入响应头
        response.setHeader(CommonVariousStrPool.HttpHeaders.AUTHORIZATION, securityToken.getProxyToken());
        response.setHeader(CommonVariousStrPool.HttpHeaders.REFRESH_AUTHORIZATION, securityToken.getProxyRefreshToken());
    }
}
```

**要点**：
- Flow 可以注入多个业务域的 Service
- Flow 内部用注释标注步骤（// 1. 查询用户、// 2. 验证密码...）
- 支持 `@Validated` + `@Valid` 进行参数校验
- 需要事务时使用 `@Transactional`

---

## 四、Job — 定时任务

业务定时任务使用 **yzj-job**（`@YzjJob`）：自带执行记录、实时日志、多实例互斥、手动触发、告警。完整用法见 `job` skill。

```java
/**
 * 订单超时处理任务
 *
 * @author hwy
 * @since 2026/03/01
 **/
@Slf4j
@Component
public class OrderTimeoutJob {
    @Resource
    private OrderService orderService;

    @YzjJob(name = "orderTimeout", cron = "0 */5 * * * ?", timeout = "4m", description = "关闭超时未支付订单")
    public String execute(JobContext ctx) {
        int closed = orderService.closeTimeoutOrders();
        ctx.log().info("关闭超时订单 {} 笔", closed);
        return "closed=" + closed;
    }
}
```

> 即使只涉及单业务，定时任务也放在 `integration/jobs/`。
> `@Scheduled` 只用于无需记录、无需多实例互斥的本地轻量维护（如刷新本地缓存）。

---

## 五、Listener — 事件监听

```java
/**
 * 数据消息确认监听器
 *
 * @author hwy
 * @since 2026/03/01
 **/
@Slf4j
@Component
public class DataMessageConfirmListener {
    @Resource
    private DataMessageRecordService dataMessageRecordService;

    @EventListener
    public void onConfirm(DataMessageConfirmEvent event) {
        // 监听业务事件并触发后续流程
    }
}
```

---

## 六、Initializer — 初始化器

继承 `BaseInitializer`，在应用启动时执行初始化逻辑。

```java
/**
 * 加载权限初始化
 *
 * @author hwy
 * @since 2026/02/20
 **/
@Order(1)  // 越小越先执行
@Component
public class LoadPermissionInitializer extends BaseInitializer {

    @Resource
    private SystemPermissionService systemPermissionService;

    @Override
    public void initialize() {
        // 加载权限到缓存
    }

    @Override
    public boolean isRequired() {
        return true;  // 失败则停止启动
    }

    // isAsync() 默认 true，同步则 return false
}
```

---

## 七、场景归属判断

| 场景 | 归属层 | 说明 |
|------|--------|------|
| 单业务 CRUD | `domain/{业务}/service` | 直接在 Service 实现 |
| 关联业务协同 | `domain/{业务}/service` | 相关 Service 间调用 |
| 多业务编排 | `integration/business/{业务}` | 需要协调多个 Service |
| 定时任务 | `integration/jobs` | 即使单业务也放 integration |
| 事件驱动 | `integration/listener` | 监听事件触发后续流程 |
| 应用启动初始化 | `integration/initializer` | 继承 BaseInitializer |

### 判断决策树

```
这个操作涉及多个业务域的写操作？
    ├── 是 → Flow（integration/business/）
    └── 否
        ├── 是定时任务？ → Job（integration/jobs/）
        ├── 是事件监听？ → Listener（integration/listener/）
        ├── 是启动初始化？ → Initializer（integration/initializer/）
        └── 是单业务 CRUD → Service（domain/{业务}/service/）
```

---

## 八、Flow 与事务边界

YZJ **不禁止** Flow 在事务中调用 RPC / HTTP / MQ，但必须遵守"提交前限定 / 提交后开放"的约束。

### 8.1 事务提交前（事务进行中）的允许范围

只允许执行以下操作：

| 操作 | 允许 | 说明 |
|------|:----:|------|
| 本地数据库写（通过 Service） | ✅ | 事务内的核心写操作 |
| **查询性** RPC / HTTP 调用 | ✅ | 仅查询数据，不产生副作用 |
| **通知性** MQ 发送 | ✅ | 仅起通知/广播作用，下游失败不影响主流程 |
| **写操作** RPC / HTTP 调用 | ❌ | 会产生外部副作用，本地事务回滚也无法撤销 |
| **业务驱动型** MQ 发送（下游有写操作） | ❌ | 同上，必须放到提交后 |

**判断标准**：如果外部操作会产生**无法回滚的副作用**，必须放到事务提交后。

### 8.2 事务提交后：使用 TransactionUtils

需要在事务提交后才能安全执行的操作（写操作 RPC / HTTP、业务驱动 MQ、缓存清理等），使用 `com.yeziji.common.utils.TransactionUtils`：

```java
@Slf4j
@Component
public class OrderCreateFlow {

    @Resource
    private OrderService orderService;
    @Resource
    private AccountService accountService;
    @Resource
    private NotifyMqProducer notifyMqProducer;
    @Resource
    private ThreadPoolTaskExecutor commonTaskExecutor;

    @Transactional(rollbackFor = Exception.class)
    public void create(AddOrderOperate operate) {
        // 1. 本地写操作（事务内）
        Long orderId = orderService.add(operate);

        // 2. 事务内：查询性 RPC 调用 ✅
        UserInfoDTO user = userRpcClient.getById(operate.getUserId());

        // 3. 事务内：通知性 MQ ✅（仅通知，下游失败不影响）
        notifyMqProducer.send(new OrderCreatedNotifyEvent(orderId));

        // 4. 事务内：账户冻结（写操作）❌ → 改用 TransactionUtils
        TransactionUtils.asyncExecuteAfterCommit(
                () -> accountService.freeze(operate.getUserId(), operate.getAmount()),
                commonTaskExecutor
        );

        // 5. 事务内：业务驱动 MQ（下游会写库）❌ → 改用 TransactionUtils
        TransactionUtils.asyncExecuteAfterCommit(
                () -> orderEventMqProducer.send(new OrderCreatedEvent(orderId)),
                commonTaskExecutor
        );
    }
}
```

### 8.3 TransactionUtils 工具方法

```java
package com.yeziji.common.utils;

/**
 * 异步事务提交后执行（事务未开启时直接异步）
 */
public class TransactionUtils {
    public static void asyncExecuteAfterCommit(
            Runnable action,
            ThreadPoolTaskExecutor threadPoolTaskExecutor) {
        // 未开启事务 → 直接异步执行
        // 已开启事务 → 注册 TransactionSynchronization.afterCommit() 回调
    }
}
```

**行为说明**：
- 若调用时未在事务上下文中（`TransactionSynchronizationManager.isActualTransactionActive() == false`），直接通过线程池异步执行
- 若已在事务上下文中，会注册到 Spring 的 `TransactionSynchronization`，事务**成功提交**后再异步执行；事务回滚则不执行

### 8.4 决策速查

```
要在 Flow 内调用外部？
    │
    ├── 查询性 RPC / HTTP        → 直接调用（事务内）
    ├── 通知性 MQ（下游不依赖结果） → 直接调用（事务内）
    ├── 写操作 RPC / HTTP        → TransactionUtils.asyncExecuteAfterCommit
    ├── 业务驱动 MQ（下游会写库）  → TransactionUtils.asyncExecuteAfterCommit
    └── 缓存失效 / 索引更新等副作用 → TransactionUtils.asyncExecuteAfterCommit
```

---

## 九、禁止事项

1. Flow 中直接操作 Mapper（应通过 Service）
2. Service 中处理跨业务域的写操作（应在 Flow 中）
3. Controller 中直接编排多个 Service（应抽取为 Flow）
4. Initializer 中不继承 BaseInitializer
5. 事务内调用**写操作型**外部 RPC/HTTP（必须用 `TransactionUtils.asyncExecuteAfterCommit`）
6. 事务内发送**业务驱动型** MQ（下游会写库的，必须用 `TransactionUtils.asyncExecuteAfterCommit`）
