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

    @Scheduled(cron = "0 */5 * * * ?")
    public void execute() {
        // 定时任务逻辑
    }
}
```

> 即使只涉及单业务，定时任务也放在 `integration/jobs/`。

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

## 八、禁止事项

1. Flow 中直接操作 Mapper（应通过 Service）
2. Service 中处理跨业务域的写操作（应在 Flow 中）
3. Controller 中直接编排多个 Service（应抽取为 Flow）
4. Initializer 中不继承 BaseInitializer
