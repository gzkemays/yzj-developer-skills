---
name: framework-usage
description: "[DEPRECATED] 此 skill 已弃用，功能已拆分至独立的组件级 skill：common（通用工具）、cache（缓存与分布式锁）、mybatis（数据库查询构建）、security（安全认证）。请直接使用对应的组件 skill。"
---

> **⚠️ DEPRECATED**: 此 skill 已弃用。请使用以下替代 skill：
> - `common` — 通用工具类、枚举、异常、SessionContext
> - `cache` — 缓存注解、分布式锁、API 调度锁
> - `mybatis` — IQueryChain 查询构建、分页排序
> - `security` — JWT/OAuth 认证、Token 上下文

# Framework 各组件功能说明及使用方法

本文档详细介绍 framework 项目中各个组件的功能及使用方法。

## 模块概览

| 模块名称 | 说明 |
|---------|------|
| yzj-common | 通用工具类、枚举、常量、模型等基础功能 |
| yzj-cache | 缓存核心实现，支持 Redis、Redisson、Caffeine |
| yzj-cache-spring-boot-starter | 缓存 Starter，注解驱动缓存操作 |
| yzj-mybatis | MyBatis-Flex 二次封装，提供链式查询 |
| yzj-security | Spring Security 封装，提供 OAuth、Token 接口 |
| yzj-security-spring-boot-starter | Security Starter，自动装配安全配置 |

---

## 一、yzj-common 通用工具包

**模块路径**: `d:\Development\Project\framework\yzj-common`

**作用**: 提供项目通用工具类、枚举、常量、模型等基础功能，应用项目应优先使用此包下的工具类。

### 1.1 常用工具类

#### SpringUtils - Spring 上下文工具类

```java
// 获取 Bean
UserService userService = SpringUtils.getBean(UserService.class);

// 动态注册 Bean
SpringUtils.registerBean("customBean", new CustomBean());

// 发布事件
SpringUtils.publishEvent(new CustomEvent());

// 获取配置属性
String value = SpringUtils.getProperty("property.key");

// 获取当前环境
String profile = SpringUtils.getActiveProfile();
```

#### DateUtils - 日期工具类

```java
// 获取日期起始时间（00:00:00）
Date begin = DateUtils.ofBegin(date);

// 获取日期结束时间（23:59:59）
Date end = DateUtils.ofEnd(date);

// 获取月初日期
Date monthBegin = DateUtils.beginOfMonth(date);

// 获取月末日期
Date monthEnd = DateUtils.endOfMonth(date);

// 追加时间单位
Date plus = DateUtils.plus(date, 1, ChronoUnit.DAYS);

// 扣减时间单位
Date minus = DateUtils.minus(date, 1, ChronoUnit.HOURS);
```

#### AesUtils / RsaUtils - 加解密工具类

```java
// AES 加密解密
String encrypted = AesUtils.encrypt(data, key);
String decrypted = AesUtils.decrypt(encrypted, key);

// RSA 加密解密
String encrypted = RsaUtils.encryptByPublicKey(data, publicKey);
String decrypted = RsaUtils.decryptByPrivateKey(encrypted, privateKey);
```

#### ThreadPoolUtils - 线程池工具类

```java
// 获取自定义线程池
ExecutorService executor = ThreadPoolUtils.getExecutor("custom-pool");
```

### 1.2 常用模型

#### CommonResult - 统一响应结果

```java
// 成功响应
return CommonResult.success(data);
return CommonResult.success();
return CommonResult.success(data, "操作成功");

// 分页响应
return CommonResult.successPage(page);

// 失败响应
return CommonResult.failed("错误信息");
return CommonResult.failed(ErrorMsgEnum.XXX);
return CommonResult.validate(bindingResult);

// 特定状态
return CommonResult.forbidden();
return CommonResult.unauthorized();
```

#### CommonPage - 分页模型

```java
// 构建分页数据
CommonPage<UserVO> page = CommonPage.build(pageEntity);
```

### 1.3 常用常量

```java
// 状态码

import com.yeziji.common.constants.CommonVariousStrPool;

CommonStatusCode.SUCCESS;  // 成功
CommonStatusCode.ERROR;     // 错误

// 符号常量
CommonVariousStrPool.Symbol.COMMA;        // 逗号
CommonVariousStrPool.Symbol.DOT;         // 点号

// HTTP 常量
HttpConstants.GET;
HttpConstants.POST;
```

---

## 二、yzj-cache 缓存核心包

**模块路径**: `d:\Development\Project\framework\yzj-cache`

**作用**: 缓存核心实现，提供 Redis、Redisson、Caffeine 两种模式的缓存封装。

### 2.1 缓存模式

| 模式 | 说明 |
|-----|------|
| Redis 模式 | 分布式缓存，支持跨 JVM |
| Caffeine 模式 | 本地缓存，性能更高 |

### 2.2 CacheService 接口方法

```java
// 基本缓存操作
void put(String key, Object value);
void put(String key, Object value, long expire, TimeUnit timeUnit);
<T> T get(String key);
<T> T getIf(String key, long expire, TimeUnit timeUnit, Supplier<T> supplier);
void remove(String key);
boolean hasKey(String key);
long getExpireTime(String key);
void expire(String key, long expire, TimeUnit timeUnit);

// 原子操作
boolean putIfAbsent(String key, Object value, long expire, TimeUnit timeUnit);
long increment(String key, long expire, TimeUnit timeUnit);

// 分布式锁
boolean lock(String key, long expire, int retryCount, long sleepMillis);
boolean releaseLock(String key);

// Hash 操作
void hashPut(String key, String hashKey, Object value);
<T> T hashGet(String key, String hashKey);
void hashRemove(String key, String hashKey);

// List 操作
void listRightPush(String key, Object value);
<T> T listRightPop(String key);

// Set 操作
long setAdd(String key, Object value);
<T> Set<T> setMembers(String key);
boolean setIsMember(String key, Object value);
```

---

## 三、yzj-cache-spring-boot-starter 缓存 Starter

**模块路径**: `d:\Development\Project\framework\yzj-cache-spring-boot-starter`

**作用**: 基于 Spring Boot 自动装配，提供注解驱动的缓存操作，支持分布式锁与本地锁。

### 3.1 启用缓存

```java
// 在启动类添加注解
@EnableYzjCache
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 3.2 缓存注解

#### @CacheRead - 读取缓存

```java
// 基本用法 - 优先从缓存读取，未命中时执行方法并写入缓存
@CacheRead(key = "user:#p0", expire = 10, timeUnit = TimeUnit.MINUTES)
public UserDTO getUserById(Long id) {
    return userMapper.selectById(id);
}

// Hash 模式
@CacheRead(key = "user:role", hashKey = "#userId", expire = 30)
public UserRoleDTO getRoleByUserId(Long userId) {
    return userRoleMapper.selectByUserId(userId);
}
```

**参数说明**:
- `key`: 缓存 key，支持 Spring EL 表达式（如 `#p0` 表示第一个参数，`#userId` 表示参数属性）
- `hashKey`: Hash 模式下使用，为空时使用普通 key-value 模式
- `expire`: 过期时间
- `timeUnit`: 时间单位

#### @CachePut - 写入缓存

```java
// 执行方法后将返回值写入缓存
@CachePut(key = "user:#p0.id", expire = 10, timeUnit = TimeUnit.MINUTES)
public UserDTO updateUser(UpdateUserOperate operate) {
    return userService.doUpdate(operate);
}
```

#### @CacheEvict - 清除缓存

```java
// 执行方法后清除指定缓存
@CacheEvict(key = "user:#p0")
public void removeUser(Long id) {
    userMapper.deleteById(id);
}

// Hash 模式清除
@CacheEvict(key = "user:role", hashKey = "#userId")
public void updateUserRole(Long userId, RoleDTO role) {
    userRoleMapper.update(userId, role);
}

// 方法执行前清除
@CacheEvict(key = "user:#p0", beforeInvocation = true)
public void deleteUser(Long id) {
    userMapper.deleteById(id);
}
```

### 3.3 分布式锁注解

#### @DistributedLock - 分布式锁

```java
// 基本用法
@DistributedLock(key = "#typeEnum.code", prefix = "biz-max-id:get")
public long getMaxIdByType(BizMaxIdRecordTypeEnum typeEnum) {
    return getMaxId(typeEnum);
}

// 完整配置
@DistributedLock(
    key = "#orderNo",
    prefix = "order:lock",
    waitTime = 5000,
    leaseTime = 30000,
    failMessage = "订单处理中，请勿重复提交",
    transactional = true
)
public void processOrder(String orderNo) {
    // 业务逻辑
}
```

**参数说明**:
- `key`: 锁 key，支持 Spring EL 表达式
- `prefix`: 锁 key 前缀，最终格式为 `{globalPrefix}lock:{prefix}:{解析后的key}`
- `waitTime`: 等待获取锁的最大时间（毫秒），默认 3000ms
- `leaseTime`: 持锁时间（毫秒），-1 启用 Redisson watchdog 自动续期
- `failMessage`: 获取锁失败时的提示信息
- `transactional`: 是否在事务内执行

### 3.4 配置参数

在 `application.yml` 中配置：

```yaml
yzj:
  cache:
    # 全局锁前缀
    lock-prefix: "lock"
    # Redis 配置
    redis:
      host: localhost
      port: 6379
      password: 
      database: 0
    # 本地缓存配置
    local:
      enabled: true
      maximum-size: 10000
      expire-after-write: 600
```

---

## 四、yzj-mybatis 数据库操作包

**模块路径**: `d:\Development\Project\framework\yzj-mybatis`

**作用**: 对 MyBatis-Flex 进行二次封装，提供 IQueryChain 链式查询和 CommonQuery 通用查询条件。

### 4.1 IQueryChain 链式查询

```java
// 创建查询链
IQueryChain.of(UserEntity.class)
    .commonWrapper()                                    // 包装通用条件（ids、创建时间、更新时间）
    .commonWrappers(UserEntity::getName)                // 关键字查询
    .commonOrderBy()                                     // 动态排序
    .defaultOrderDescBy(UserEntity::getCreateTime)      // 默认排序
    .pageAs();                                          // 分页查询转换为 VO
```

#### 常用方法

| 方法 | 说明 |
|-----|------|
| `commonWrapper()` | 包装通用条件（ids、createTimeRange、updateTimeRange） |
| `commonWrappers(LambdaGetter... keywordKeys)` | 关键字 AND 查询 |
| `commonOrKeywords(LambdaGetter... keywordKeys)` | 关键字 OR 查询 |
| `commonOrderBy()` | 动态排序，根据前端传入的 orderBy 参数排序 |
| `defaultOrderDescBy(LambdaGetter... columns)` | 默认降序排序，前端未传排序时使用 |
| `defaultOrderAscBy(LambdaGetter... columns)` | 默认升序排序 |
| `pageAs()` | 分页查询，返回 VO 列表 |
| `oneAs()` | 查询单个对象 |
| `listAs()` | 查询列表 |

#### 使用示例

```java
// 分页查询用户
public CommonResult<CommonPage<UserVO>> queryUserPage(UserQuery query) {
    Page<UserVO> page = IQueryChain.of(query, UserEntity.class)
        .select(UserEntity::getId, UserEntity::getName, UserEntity::getPhone)
        .commonWrappers(UserEntity::getName, UserEntity::getPhone)
        .commonOrderBy()
        .defaultOrderDescBy(UserEntity::getCreateTime)
        .pageAs();
    return CommonResult.successPage(page);
}

// 根据 ID 查询
public Optional<UserVO> getUserById(Long id) {
    CommonQuery query = new CommonQuery();
    query.setIds(List.of(id));
    return IQueryChain.of(query, UserEntity.class)
        .oneAsOpt();
}
```

### 4.2 CommonQuery 通用查询条件

```java
CommonQuery query = new CommonQuery();
query.setIds(List.of(1L, 2L));                  // ID 列表查询
query.setKeyword("张三");                         // 关键字查询
query.setCreateTimeRange(TimeRange.of(start, end)); // 创建时间范围
query.setUpdateTimeRange(TimeRange.of(start, end)); // 更新时间范围
query.setOrderBy(List.of(new OrderBy("create_time", true))); // 排序
query.setPageNumber(1);                         // 页码
query.setPageSize(10);                          // 每页数量
```

### 4.3 数据加解密

#### @Encryption 注解

```java
// 在实体字段上使用
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

### 4.4 公共字段自动填充

框架自动处理创建时间、更新时间等公共字段，通过 `DefaultOnInsertListener` 和 `DefaultOnUpdateListener` 实现。

---

## 五、yzj-security 安全认证包

**模块路径**: `d:\Development\Project\framework\yzj-security`

**作用**: 对 Spring Security 进行封装，提供 Token 方法接口、OAuth 授权接口，满足常规鉴权需求。

### 5.1 核心接口

#### IJwtTokenGenerate - JWT Token 生成

```java
public class CustomJwtTokenGenerate implements IJwtTokenGenerate {
    @Override
    public SecurityToken generate(Object claims) {
        // 生成 Token
    }
    
    @Override
    public SecurityToken renewal(String refreshProxyToken) {
        // 续期 Token
    }
    
    @Override
    public SecurityToken copy(String proxyToken) {
        // 复制 Token
    }
    
    @Override
    public boolean isExpired(String token) {
        // 判断是否过期
    }
    
    @Override
    public void deprecated(SecurityToken securityToken) {
        // 弃用 Token
    }
}
```

#### OauthAuthorizationService - OAuth 授权服务

```java
// 生成授权码
String code = oauthAuthorizationService.generateCode(clientId, userId, scopes, redirectUri);

// 授权码交换令牌
OauthTokenResponse response = oauthAuthorizationService.exchangeCode(code, clientId, clientSecret, redirectUri);

// 刷新令牌
OauthTokenResponse response = oauthAuthorizationService.refreshToken(refreshToken, clientId, clientSecret);
```

#### DynamicSecurityAuth - 动态安全认证

```java
public interface DynamicSecurityAuth {
    TenantInfo getTenantInfo();          // 获取租户信息
    Set<String> getIgnoreUrls();        // 获取免鉴权地址
    Set<String> getPermissionUrls();    // 获取需要权限的地址
}
```

### 5.2 Token 上下文

```java
// 获取当前登录用户信息
SecurityToken token = SecurityTokenContext.get();

// 获取用户 ID
Long userId = SecurityTokenContext.getUserId();

// 获取租户 ID
String tenantId = SecurityTokenContext.getTenantId();
```

---

## 六、yzj-security-spring-boot-starter 安全认证 Starter

**模块路径**: `d:\Development\Project\framework\yzj-security-spring-boot-starter`

**作用**: 对 Security 进行应用级封装，默认装配过滤器等，使授权登录统一化。

### 6.1 启用安全认证

```java
// 方式一：启用 JWT
@EnableYzjJwt
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

// 方式二：启用 OAuth
@EnableYzjOauth
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

// 方式三：同时启用
@EnableYzjSecurity
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 6.2 配置参数

在 `application.yml` 中配置：

```yaml
yzj:
  security:
    # JWT 配置
    jwt:
      enabled: true
      secret: your-secret-key
      access-token-validity: 3600       # Access Token 有效期（秒）
      refresh-token-validity: 604800    # Refresh Token 有效期（秒）
    
    # OAuth 配置
    oauth:
      enabled: true
      token-endpoint: /oauth/token
      code-expire-seconds: 300
      authorization-endpoint: /oauth/authorize
```

### 6.3 SecurityFilterChain 自动装配

框架自动配置以下组件：
- JWT 过滤器（JwtFilter）
- 日志过滤器（LoggerFilter）
- CORS 配置
- 动态权限管理器（DynamicAuthorizationManager）
- 认证异常处理（RequestAuthenticationEntryPoint）
- 权限异常处理（RequestAccessDeniedHandler）

---

## 七、使用建议

### 7.1 技术选型建议

| 场景 | 推荐使用 |
|-----|---------|
| 工具类 | 优先使用 yzj-common 下的工具类 |
| 缓存操作 | 使用 yzj-cache-spring-boot-starter 注解方式 |
| 数据库查询 | 使用 yzj-mybatis 的 IQueryChain 链式查询 |
| 用户认证 | 使用 yzj-security 定义的接口 |
| Web 安全 | 使用 yzj-security-spring-boot-starter 自动配置 |