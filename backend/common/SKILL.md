---
name: common
description: yzj-common 通用基础模块使用指南。当需要使用工具类（Coll/Opt/Str/Asserts/DataUtils/DateUtils 等）、创建枚举（CommonEnum/ErrorMsgEnum）、异常处理（ApiException）、统一响应（CommonResult）、SessionContext 上下文、初始化器（BaseInitializer）、常量规范时使用此 skill。
---

# yzj-common 通用基础模块

包根路径：`com.yeziji.common`

---

## 一、统一响应 CommonResult\<T\>

```java
// 成功
CommonResult.success(data);
CommonResult.success(data, UserVO::convert);   // 带转换
CommonResult.successPage(page);                // 分页
CommonResult.successOf("操作成功");            // 仅消息

// 失败
CommonResult.failed(SomeErrorMsg.XXX);         // 优先用 ErrorMsgEnum
CommonResult.failed("错误消息");
CommonResult.forbidden();
CommonResult.unauthorized();
```

---

## 二、枚举规范

所有业务枚举实现 `CommonEnum`，错误枚举实现 `ErrorMsgEnum`。使用 `@Getter` + `@AllArgsConstructor` 代替手写 getter。

```java
// 普通枚举 — CommonEnum 父接口已标注 @EnumValue，子类无需重复标注
@Getter
@AllArgsConstructor
public enum StatusEnum implements CommonEnum {
    ENABLE(1), DISABLE(0);
    private final int code;
}

// 错误枚举
@Getter
@AllArgsConstructor
public enum UserErrorMsg implements ErrorMsgEnum {
    USER_NOT_FOUND(-1001, "用户不存在");
    private final int code;
    private final String msg;
}
```

---

## 三、异常规范

### 3.1 ApiException — 通用业务异常（默认使用）

`ApiException` 是框架的**通用业务异常**，被全局异常处理器自动捕获并转换为 `CommonResult.failed(...)` 响应。**绝大多数业务异常都应使用它**：

```java
// 业务异常默认统一使用 ApiException
throw new ApiException(UserErrorMsg.USER_NOT_FOUND);

// 禁止直接 throw new RuntimeException("...")
```

**行为**：抛出后 → 全局异常处理器 → 自动返回 `CommonResult.failed(errorMsg)`，无需业务代码兜底处理。

### 3.2 {Business}Exception — 自定义业务异常（特殊处理场景）

当业务逻辑需要**对特定异常做非 `CommonResult.failed` 的处理**时（即需要 catch 后改变默认行为），可以定义自定义 `{Business}Exception`：

**典型使用场景**：
- 调用方需要 catch 后**降级返回成功响应**（不视为 failed）
- 调用方需要 catch 后**重试 / 走分支逻辑**
- 在跨业务 Flow 中需要区分具体异常类型来决定回滚策略

```java
// 1. 定义自定义异常（可继承 ApiException 或 RuntimeException，按场景选择）
public class UserDuplicateException extends ApiException {
    public UserDuplicateException() {
        super(UserErrorMsg.USER_DUPLICATE);
    }
}

// 2. Service 抛出
public void add(AddUserOperate operate) {
    if (existsByUsername(operate.getUsername())) {
        throw new UserDuplicateException();
    }
    // ...
}

// 3. Flow 中特殊处理：catch 后改写为"幂等成功"而非 failed
try {
    userService.add(operate);
} catch (UserDuplicateException e) {
    log.info("用户已存在，按幂等成功处理, username={}", operate.getUsername());
    return; // 不抛出，不返回 failed
}
```

### 3.3 异常选择决策

```
抛出业务异常时：
    │
    ├── 调用方不需要特殊处理（直接走全局异常处理器 → failed）
    │       → 使用 ApiException(ErrorMsgEnum) ✅
    │
    └── 调用方需要 catch 后做非 failed 处理（降级/重试/幂等）
            → 自定义 {Business}Exception ✅
```

**原则**：
- ApiException 是**默认选择**，不要为每个错误码都创建专属异常类
- 只有"需要被 catch 后改写行为"的场景，才创建 `{Business}Exception`
- 自定义异常通常以业务命名（如 `UserDuplicateException`、`OrderExpiredException`），表达"什么业务场景"

---

## 四、SessionContext 上下文

线程级别的会话上下文，由框架拦截器在请求进入时注入，业务代码任意位置可读取。

```java
// 获取当前登录用户
IUserDetails user = SessionContext.getUserDetails();
Long userId = SessionContext.getUserDetailsAttribute(IUserDetails::getUserId);

// 获取当前租户
TenantInfo tenant = SessionContext.getTenant();
Long tenantId = SessionContext.getTenantAttribute(TenantInfo::getTenantId);

// 获取 Servlet 信息
String ip = SessionContext.getServletInfoAttribute(ServletInfo::getIp);

// 判断状态
SessionContext.exist();          // 是否登录
SessionContext.isSuperAdmin();   // 是否超管

// 异步线程中必须通过 ThreadPoolUtils，否则上下文丢失
ThreadPoolUtils.execute(() -> {
    // 此处 SessionContext 仍然可用
    doSomething();
}, taskExecutor);
```

> **注意**：`SessionContext.clear()` 由框架自动调用，业务代码不要手动清除。直接使用 `CompletableFuture.runAsync` 会丢失上下文，必须改用 `ThreadPoolUtils.execute`。

---

## 五、工具类速查

### 5.1 ext 扩展工具（无状态，直接静态调用）

#### Coll — 集合工具

```java
Coll.isEmpty(list)                              // null 安全判空
Coll.transforms(list, VO::of)                   // 列表类型转换
Coll.streamToMap(list, T::getId)                // list → Map（key 冲突异常）
Coll.streamToMap(list, T::getId, true)          // list → Map（取最新值）
Coll.streamToGroupBy(list, T::getType)          // list → Map<K, List<T>>
Coll.distinctBy(list, T::getId)                 // 按字段去重
Coll.splitterCommaStr("a,b,c")                  // 逗号分割为 List
Coll.joinerCommaStr(list)                       // List 拼接为逗号字符串
Coll.nests(listOfLists)                         // List<List<T>> 展平为 List<T>

// 差异对比
Coll.compare(newList, dbList)
    .addSample(T::getId, D::getId)
    .existsDo((t, d) -> update(t))              // 两边都有 → 更新
    .notExistsDo(t -> insert(t))                // 新增的 → 插入
    .contrastNotExistsDo(d -> delete(d))        // 删除的 → 删除
    .execute();
```

#### Opt — Optional 辅助

```java
Opt.nullElse(value, defaultVal)                 // null → defaultVal
Opt.nullEmpty(str)                              // null → ""
Opt.nullTrue(bool)                              // null → true
Opt.notNullThen(obj, consumer)                  // 非 null 才执行
```

#### Str — 字符串工具

```java
Str.notBlankThen(str, consumer)                 // 非空才执行
Str.isBlankElse(str, "默认值")                  // 空则返回默认值
Str.contain("api/*", "/api/user", false)        // 支持 * 通配符匹配
Str.toCamelCase("user_name", '_')               // 下划线转驼峰
Str.formatNumber(5, 4)                          // → "0005"
```

#### Asserts — 断言（失败直接抛 ApiException）

```java
Asserts.notNull(obj, ErrorMsg.NOT_FOUND)        // 为 null 则抛异常，返回 obj
Asserts.notBlank(str, ErrorMsg.PARAM_ERROR)     // 空字符串则抛异常
Asserts.isNull(obj, ErrorMsg.ALREADY_EXISTS)    // 不为 null 则抛异常
Asserts.isTruth(bool, ErrorMsg.FAILED)          // 不为 true 则抛异常
Asserts.equals(a, b, ErrorMsg.NOT_MATCH)        // 不相等则抛异常
Asserts.gt(num, 0L, ErrorMsg.INVALID)           // num < 0 则抛异常
Asserts.error(ErrorMsg.FORBIDDEN)               // 主动抛异常
```

### 5.2 功能性工具

#### DataUtils — 数据转换

```java
DataUtils.toJson(obj)                           // 对象 → JSON（保留 null 字段）
DataUtils.fromJson(json, UserDTO.class)         // JSON → 对象
DataUtils.fromBean(source, TargetDTO.class)     // Bean → Bean（JSON 转换，字段名匹配）
DataUtils.convertBean(source, TargetDTO.class)  // Bean → Bean（BeanCopier 浅拷贝，性能更好）
DataUtils.setIfNotNull(value, obj::setField)    // 非 null 才 set
```

#### DateUtils — 日期工具

```java
DateUtils.formatTime(1500L)                     // → "1s"
DateUtils.ofBegin(date)                         // 当天 00:00:00
DateUtils.ofEnd(date)                           // 当天 23:59:59
DateUtils.plus(date, 7, ChronoUnit.DAYS)        // 加 7 天
DateUtils.minus(date, 1, ChronoUnit.MONTHS)     // 减 1 个月
DateUtils.beginOfMonth(date)                    // 本月第一天
DateUtils.toLocalDateTime(date)                 // Date → LocalDateTime
```

#### 其他工具

```java
// NanoIdUtils — 随机 ID 生成
NanoIdUtils.randomNanoId()                      // 21 位（含特殊符号）
NanoIdUtils.randomNotSymbolNaoId()              // 21 位（仅字母数字）
NanoIdUtils.randomNaoId(32)                     // 指定长度

// SpringUtils — Spring 容器访问
SpringUtils.getBean(UserService.class)
SpringUtils.getBeansOfType(BaseInitializer.class)
SpringUtils.getProperty("spring.application.name")
SpringUtils.publishEvent(new UserCreatedEvent(user))

// LockUtils — 本地可重入锁
LockUtils lock = LockUtils.newInstance(true);   // true = 公平锁
lock.execute(() -> criticalSection());          // 阻塞执行
boolean ok = lock.tryExecute(() -> tryWork());  // 非阻塞

// ThreadPoolUtils — 异步执行（自动传递 SessionContext）
ThreadPoolUtils.execute(() -> asyncTask(), executor);
String result = ThreadPoolUtils.execute(() -> compute(), 10, executor); // 超时 10s

// ResponseUtils — 直接写出 HTTP 响应（Filter/Security 场景）
ResponseUtils.writeJson(response, CommonResult.unauthorized());
```

### 5.3 辅助工具

```java
// KeyGenerateAid — 雪花算法风格 ID（需注入为单例）
long id = keyGenerateAid.getKey(KeyGenerateAid.getWorkId());

// SelfAssociationAid — 自关联树结构辅助（菜单/组织树）
SelfAssociationAid<T> aid = new SelfAssociationAid<>(treeList);
List<T> flatList = aid.getFlatten(T::getChildren);
```

---

## 六、初始化器规范

```java
@Order(1)  // 越小越先执行
@Component
public class MyInitializer extends BaseInitializer {
    @Override
    public void initialize() { /* 初始化逻辑 */ }

    @Override
    public boolean isRequired() { return true; } // 失败则停止启动
    // isAsync() 默认 true，同步则 return false
}
```

---

## 七、常量规范

- 状态码用 `CommonStatusCode` 接口常量（SUCCESS=0, ERROR=-1）
- 字符串常量用 `CommonVariousStrPool`（EMPTY、Symbol.COMMA、HttpHeaders.AUTHORIZATION 等）
- 不要在业务代码中硬编码 0/-1 作为状态码

---

## 八、常见错误

| 错误 | 正确做法 |
|------|----------|
| 直接 `return null` 或空 Map | 用 `Coll.empty()` / `new HashMap<>(0)` |
| 枚举未实现 `CommonEnum` | 实现接口（父接口已含 `@EnumValue`，子类无需重复标注） |
| 抛出 `RuntimeException` | 抛出 `ApiException(ErrorMsgEnum)` |
| 返回 `Map<String,Object>` | 定义具体 VO 类并用 `CommonResult<VO>` |
| 用 `@Builder` | 用 `@SuperBuilder`（支持继承） |
| 异步线程中读不到用户信息 | 用 `ThreadPoolUtils.execute` 代替裸 `CompletableFuture` |
| 手写 Bean 互转逻辑 | 用 `DataUtils.convertBean` 或 `DataUtils.fromBean` |
| 手写日期加减 | 用 `DateUtils.plus/minus/ofBegin/ofEnd` |
| 手动生成业务 ID（UUID） | 用 `NanoIdUtils` 或注入 `KeyGenerateAid` |
