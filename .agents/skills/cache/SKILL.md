---
name: cache
description: "yzj-cache-spring-boot-starter 缓存与分布式锁使用指南。当需要使用缓存注解（@CacheRead/@CachePut/@CacheEvict）、分布式锁（@DistributedLock）、API 调度锁（@ApiLock）、CacheService 编程式 API、Redis/Caffeine 缓存配置时使用此 skill。"
---

# yzj-cache-spring-boot-starter 缓存与分布式锁

---

## 一、快速接入

### 1.1 添加依赖

```xml
<dependency>
    <groupId>com.yeziji</groupId>
    <artifactId>yzj-cache-spring-boot-starter</artifactId>
</dependency>
```

Redis 模式额外引入：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
<!-- 分布式锁（可选） -->
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-boot-starter</artifactId>
</dependency>
```

### 1.2 启动类启用

```java
@SpringBootApplication
@EnableYzjCache
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 1.3 配置

```yaml
yzj:
  cache:
    type: local       # local（默认）或 redis
    prefix: myapp:   # 全局 key 前缀（可选）
    lock:
      key-prefix: lock  # 锁 key 前缀（默认 lock）
```

Redis 模式还需配置 Spring Redis 连接：

```yaml
spring:
  data:
    redis:
      host: localhost
      port: 6379
```

---

## 二、缓存注解

key 最终格式：`{globalPrefix}{prefix}:{key解析结果}`

支持的 key 表达式：`#paramName`、`#p0`、`#p0.field`（嵌套属性）

### @CacheRead — 读缓存（Cache-Aside）

缓存未命中时执行方法并写入缓存。

```java
// 基本用法
@CacheRead(prefix = "user", key = "#p0", expire = 10, timeUnit = TimeUnit.MINUTES)
public UserDTO getUserById(Long id) { ... }

// Hash 模式
@CacheRead(prefix = "user:role", hashKey = "#userId", expire = 30)
public UserRoleDTO getRoleByUserId(Long userId) { ... }

// 防缓存穿透（缓存 null 值）
@CacheRead(prefix = "user", key = "#p0", nullable = true)
public UserDTO findUser(Long id) { ... }

// 自定义 key 生成器
@CacheRead(prefix = "user", keyGenerator = UserCacheKeyGenerator.class)
public UserDTO getUserByQuery(UserQuery query) { ... }
```

### @CachePut — 写缓存

```java
@CachePut(prefix = "user", key = "#p0.id", expire = 10, timeUnit = TimeUnit.MINUTES)
public UserDTO updateUser(UpdateUserOperate operate) { ... }
```

### @CacheEvict — 清除缓存

支持 `@Repeatable`，可在同一方法上标注多个。

```java
// 方法执行后清除
@CacheEvict(prefix = "user", key = "#p0")
public void removeUser(Long id) { ... }

// 同时清除多个缓存
@CacheEvict(prefix = "user", key = "#p0")
@CacheEvict(prefix = "user:role", key = "#p0")
public void removeUser(Long id) { ... }

// 方法执行前清除
@CacheEvict(prefix = "user:role", hashKey = "#userId", beforeInvocation = true)
public void updateUserRole(Long userId, RoleDTO role) { ... }
```

### 自定义 key 生成器

```java
public class UserCacheKeyGenerator implements CacheKeyGenerator {

    @Override
    public String generate(Method method, Object[] args) {
        UserQuery query = (UserQuery) args[0];
        return query.getTenantId() + ":" + query.getUserId();
    }

    @Override
    public String generateHashKey(Method method, Object[] args) {
        UserQuery query = (UserQuery) args[0];
        return query.getRole();   // 非空 → 使用此值作为 hashKey
        // return "";             // 空字符串 → 回退到注解的 hashKey 表达式
    }
}
```

---

## 三、分布式锁 @DistributedLock

- 本地模式：使用 JVM 内本地锁
- Redis 模式（含 redisson 依赖）：自动切换为 Redisson 分布式锁，支持 watchdog 自动续期
- 获取锁失败时抛出异常

```java
// 基本用法
@DistributedLock(key = "#typeEnum.code", prefix = "biz-max-id:get")
public long getMaxIdByType(BizMaxIdRecordTypeEnum typeEnum) { ... }

// 自定义等待时间 + 持锁时间（-1 启用 watchdog）
@DistributedLock(key = "#p0", prefix = "pay", waitTime = 5000, leaseTime = -1,
    failMessage = "支付处理中，请勿重复提交")
public void pay(Long orderId) { ... }

// 事务内执行（锁在事务提交/回滚后释放）
@DistributedLock(key = "#p0", prefix = "stock", transactional = true)
public void deductStock(Long skuId) { ... }
```

| 属性 | 默认值 | 说明 |
|------|--------|------|
| `key` | `""` | key 表达式，空时用 `类名:方法名` |
| `prefix` | `""` | key 前缀 |
| `waitTime` | 3000ms | 等待获取锁超时 |
| `leaseTime` | -1 | 持锁时间，-1 = watchdog 续期 |
| `failMessage` | 操作频繁... | 失败提示 |
| `transactional` | false | 是否在事务内执行 |

---

## 四、API 调度锁 @ApiLock

限制接口访问频率，防止频繁调用。支持多维度组合：`IP`、`USER_ID`、`PARAMS`、`CUSTOM`。

```java
// IP 维度，1秒内不允许重复请求，超频封禁10秒
@ApiLock(acceptInterval = 1000, banDuration = 10000)
public Result submit(OrderDTO order) { ... }

// 1秒内最多5次
@ApiLock(acceptInterval = 1000, maxAttempts = 5, banDuration = 30000)
public Result query(QueryDTO query) { ... }

// 用户维度 + 参数维度
@ApiLock(dimensions = {ApiLockDimension.USER_ID, ApiLockDimension.PARAMS}, acceptInterval = 500)
public Result pay(PayDTO pay) { ... }

// 自定义维度
@ApiLock(dimensions = {ApiLockDimension.CUSTOM}, customKey = "#p0.version", acceptInterval = 2000)
public Result query(QueryDTO query) { ... }
```

自定义降级处理（默认抛出异常）：

```java
@Component
public class MyDegradationHandler implements ApiLockDegradationHandler {
    @Override
    public Object handle(ProceedingJoinPoint joinPoint, ApiLock apiLock) {
        return Result.fail("请求过于频繁，请稍后重试");
    }
}

@ApiLock(acceptInterval = 1000, degradation = MyDegradationHandler.class)
public Result submit(OrderDTO order) { ... }
```

---

## 五、CacheService 编程式 API

```java
@Resource
private CacheService cacheService;

// 基本操作
cacheService.put(key, value);
cacheService.put(key, value, 10, TimeUnit.MINUTES);
cacheService.get(key);
cacheService.getIf(key, 10, TimeUnit.MINUTES, () -> loadFromDb());
cacheService.remove(key);
cacheService.hasKey(key);
cacheService.expire(key, 10, TimeUnit.MINUTES);

// 原子操作
cacheService.putIfAbsent(key, value, 10, TimeUnit.MINUTES);
cacheService.increment(key, 10, TimeUnit.MINUTES);

// 分布式锁
cacheService.lock(key, 30000, 3, 100);
cacheService.releaseLock(key);

// Hash / List / Set 操作
cacheService.hashPut(key, hashKey, value);
cacheService.hashGet(key, hashKey);
cacheService.listRightPush(key, value);
cacheService.setAdd(key, value);
cacheService.setMembers(key);
```

---

## 六、常见错误

| 问题 | 原因 | 解决 |
|------|------|------|
| 启动报 NoSuchBeanDefinitionException: CacheService | 未加 `@EnableYzjCache` | 启动类加注解 |
| 本地模式下分布式锁不生效 | 本地锁仅 JVM 内有效 | 多实例部署需引入 redisson + Redis |
| Redis 模式启动失败 | 缺少 redis starter 或未配置连接 | 添加依赖并配置 `spring.data.redis.*` |
| `@CacheEvict` 不清除 Hash 整体 | hashKey 有值时只删 hashKey | 需删整个 key 时不设 hashKey |
| `@ApiLock` USER_ID 维度无效 | 需在 request attribute 中提供 userId | 确保 userId 已存入 request |
