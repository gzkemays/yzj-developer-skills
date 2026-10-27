# YZJ 后端日志规范

---

## 一、日志门面与声明

**统一使用 SLF4J 门面**（通过 Lombok 的 `@Slf4j` 自动生成），底层默认是 Logback。

```java
@Slf4j
@Component
public class OrderCreateFlow {
    public void create(AddOrderOperate operate) {
        log.info("订单创建开始, userId={}, amount={}", operate.getUserId(), operate.getAmount());
        // ...
    }
}
```

**禁止**：
- 直接 `import org.apache.logging.log4j.Logger;`（绕过 SLF4J 门面）
- 直接 `import ch.qos.logback.classic.Logger;`（绑死实现）
- 手写 `private static final Logger logger = LoggerFactory.getLogger(...)`（用 `@Slf4j` 即可）
- 使用 `System.out.println()` / `System.err.println()` / `e.printStackTrace()`

---

## 二、占位符 vs 字符串拼接

**必须使用占位符（`{}`）**，禁止字符串拼接：

```java
// ✅ 正确：占位符。debug/info 级别未启用时不会执行参数计算
log.info("订单查询成功, orderId={}, status={}", orderId, status);

// ❌ 错误：字符串拼接。即使日志级别未启用也会执行拼接，浪费 CPU
log.info("订单查询成功, orderId=" + orderId + ", status=" + status);

// ❌ 错误：String.format 同样有性能问题
log.info(String.format("订单查询成功, orderId=%d", orderId));
```

---

## 三、异常打印姿势

**异常对象必须作为最后一个参数传入**（SLF4J 会自动识别并打印完整堆栈）：

```java
// ✅ 正确：异常作为最后一个参数
try {
    orderService.add(operate);
} catch (Exception e) {
    log.error("订单创建失败, userId={}, amount={}", operate.getUserId(), operate.getAmount(), e);
    throw new ApiException(OrderErrorMsg.CREATE_FAILED);
}

// ❌ 错误：把异常拼到消息里，丢失堆栈
log.error("订单创建失败: " + e.getMessage());

// ❌ 错误：e.printStackTrace() 直接打到 stderr，不走日志系统
e.printStackTrace();

// ❌ 错误：catch 后吞异常
try { ... } catch (Exception e) { }
```

---

## 四、日志级别选择

| 级别 | 用途 | 生产环境 |
|------|------|----------|
| `error` | 系统逻辑出错、未预期异常、需要告警 | ✅ 输出 |
| `warn` | 业务规则告警、入参问题、降级触发、可恢复异常 | ✅ 输出 |
| `info` | 关键业务节点（请求入口、关键状态变更、外部调用结果） | ✅ 输出 |
| `debug` | 调试细节、变量值、分支判断 | ❌ 禁止输出 |
| `trace` | 极细粒度跟踪 | ❌ 禁止输出 |

### 级别选择原则

- **业务异常用 `warn`**（如"用户不存在"、"订单状态不对"等可预期错误），**不要用 `error`**
- **`error` 只用于真正需要告警的系统级问题**（如外部服务不可达、数据库异常、未捕获异常）
- **关键链路入口 + 关键状态变更** 打 `info`，避免高频 `info` 刷屏
- **不要在循环里高频 `info` / `warn`**，必要时聚合后输出

```java
// ✅ 正确：业务异常用 warn
try {
    User user = userService.getDtoById(id);
} catch (ApiException e) {
    log.warn("用户不存在, userId={}", id);
    throw e;
}

// ❌ 错误：把所有异常都打 error
try {
    User user = userService.getDtoById(id);
} catch (Exception e) {
    log.error("查询用户出错", e);  // 业务"用户不存在"不是 error
    throw e;
}
```

---

## 五、敏感信息保护

**禁止打印**：
- 密码（明文 / 加密后都禁止）
- 完整的 Token / refreshToken / Session
- 完整的身份证号、银行卡号、手机号（生产环境）
- 加密密钥、密钥种子
- HTTP 请求 / 响应的完整 Body（包含上述任一敏感字段时）

**正确做法**：脱敏后打印或直接不打印。

```java
// ✅ 正确：脱敏
log.info("用户登录, username={}, mobile={}", username, DataUtils.maskMobile(mobile));

// ❌ 错误：直接打印明文敏感字段
log.info("用户登录, username={}, password={}", username, password);

// ❌ 错误：打印完整 token
log.info("生成 token 成功, token={}", securityToken.getProxyToken());
// ✅ 正确：只打印关键信息
log.info("生成 token 成功, userId={}, expireSeconds={}", userId, expireSeconds);
```

---

## 六、日志输出格式（强制）

### 6.1 标准格式

```
[{业务动作}] {内容说明}: field1={}, field2={}, field3={}
```

**必须**以 `[{业务}]` 开头标注当前业务动作，后接**一个英文空格**，再接日志内容。

### 6.2 示例

```java
// ✅ info：业务关键节点
log.info("[创建订单] userId={}, orderNo={}", userId, orderNo);
log.info("[新增用户] 注册成功: userId={}, username={}", userId, username);
log.info("[用户登录] username={}, ip={}", username, ip);

// ✅ warn：业务告警
log.warn("[订单查询] 订单不存在: orderId={}", orderId);
log.warn("[状态变更] 状态不匹配: orderId={}, expected={}, actual={}", orderId, expected, actual);

// ✅ error：系统异常（异常对象必须作为最后一个参数）
log.error("[新增用户] 新增失败: {}", e.getMessage(), e);
log.error("[支付网关] 调用失败: orderId={}, gateway={}", orderId, gateway, e);
log.error("[订单创建] 数据库写入异常: userId={}", userId, e);
```

### 6.3 反例

```java
// ❌ 缺少 [业务] 前缀
log.info("订单创建成功, orderId={}, userId={}", orderId, userId);

// ❌ [业务] 后没有空格
log.info("[创建订单]userId={}, orderNo={}", userId, orderNo);

// ❌ 用 - 或 : 代替空格
log.info("[创建订单]-userId={}", userId);
log.info("[创建订单]:userId={}", userId);

// ❌ 业务标记使用英文驼峰而非中文业务动词
log.info("[CreateOrder] userId={}", userId);

// ❌ 业务标记过长（应短小精炼）
log.info("[创建订单并扣减库存同时通知积分服务] userId={}", userId);
```

### 6.4 `[{业务}]` 命名约定

- **用中文业务动词短语**（与 PRD / 需求文档语言保持一致），便于运维和产品快速定位
- **2-6 个汉字**为宜，避免过长
- **同一方法内统一**：一个 Service 方法 / Flow 方法内的所有日志，业务前缀保持一致

```java
// ✅ 同方法内统一前缀
public void createOrder(AddOrderOperate operate) {
    log.info("[创建订单] 开始: userId={}", operate.getUserId());
    // ...
    log.info("[创建订单] 订单写入成功: orderId={}", orderId);
    // ...
    log.warn("[创建订单] 库存不足: skuId={}", skuId);
    // ...
    log.error("[创建订单] 失败: {}", e.getMessage(), e);
}

// ❌ 同方法内前缀混乱
public void createOrder(AddOrderOperate operate) {
    log.info("[订单创建] 开始: userId={}", operate.getUserId());
    log.info("[Order] 写入成功: orderId={}", orderId);
    log.warn("[扣减库存] 库存不足: skuId={}", skuId);
}
```

### 6.5 注意事项

- **关键 ID 必须打印**（orderId、userId、tenantId 等），便于排查
- **字段用 `=` 连接**而非空格，便于日志系统提取结构化字段
- **多字段用 `,` 分隔**
- **`error` 必须以 `e.getMessage()` 作为占位符内容、`e` 作为最后参数**（保留异常消息 + 完整堆栈）
- **避免冗长**：一条日志不超过 200 字符为佳，超长拆多条

---

## 七、AOP / 切面中的日志

`support/aspect/` 下的切面可统一打印接口入参、出参、耗时，**业务代码内不需要重复打印**：

```java
// 框架/项目级 LogAspect 已统一记录 Controller 层 in/out + 耗时
// 业务代码内只打印业务关键节点即可，不要重复打日志
```

> 框架的统一入口即 `yzj-security-spring-boot-starter` 的 `LoggerFilter`，它默认打**全量**请求 / 响应体——含敏感 payload 的接口必须配忽略清单，见第九节。

---

## 八、禁止事项清单

| # | 禁止事项 | 严重程度 |
|---|----------|:--------:|
| 1 | 使用 `System.out.println()` / `System.err.println()` | 🔴 严重 |
| 2 | 使用 `e.printStackTrace()` | 🔴 严重 |
| 3 | 字符串拼接代替占位符 | 🟡 警告 |
| 4 | 异常对象未作为最后一个参数传入 log.error/warn | 🟡 警告 |
| 5 | 打印密码、Token、完整身份证 / 银行卡 / 手机号 | 🔴 严重 |
| 6 | 业务可预期异常用 `error` 级别（应用 `warn`） | 🟡 警告 |
| 7 | 生产环境输出 `debug` / `trace` 日志 | 🔴 严重 |
| 8 | `catch (Exception e) {}` 吞异常不打日志 | 🔴 严重 |
| 9 | 关键操作（写库、外调）日志中缺少业务 ID | 🟡 警告 |
| 10 | 循环内高频 `info` / `warn`（应聚合或降级 debug） | 🟡 警告 |
| 11 | 日志内容未以 `[{业务}]` 开头 | 🟡 警告 |
| 12 | `[{业务}]` 与正文之间未使用空格分隔 | 🟡 警告 |
| 13 | 同一方法内业务前缀不一致 | 🟡 警告 |
| 14 | `error` 级别只传 `e.getMessage()` 不传异常对象 `e`（丢失堆栈） | 🔴 严重 |
| 15 | 含敏感 payload 的接口未进 `yzj.logger.ignore-request-url` / `ignore-response-url`（LoggerFilter 打全量 body） | 🔴 严重 |

---

## 九、框架级请求 / 响应日志（LoggerFilter）——敏感数据的真正出口

`yzj-security-spring-boot-starter` 自动装配的 `LoggerFilter` 在 `yzj.logger.enabled=true` 时，**把每个非 multipart 请求的完整 body 和完整响应 body 打进 INFO 日志**。这意味着第五节的约束在框架层被绕过：业务代码一行敏感日志都没打，密码、Token、卡号、敏感配置照样整份落盘。

**业务代码不打敏感日志 ≠ 敏感数据不入日志。** 真正的出口是这个过滤器。

### 9.1 配置

```yaml
yzj:
  logger:
    enabled: true
    ignore-url:                 # 整条请求 / 响应日志都不打（健康检查、高频轮询）
      - /actuator/**
    ignore-request-url:         # 只省略请求参数（登录、改密、绑卡、密钥上传 …）
      - /v1/admin/auth/login
      - /v1/admin/user/password/**
      - /v1/merchant/card/bind
    ignore-response-url:        # 只省略响应体（返回 Token、明文配置、导出敏感数据 …）
      - /v1/admin/auth/login
      - /v1/admin/config/plaintext/**
```

配置后仍保留方法、URI、租户、用户 ID、IP、耗时——排障信息不丢，只是 payload 不打。地址走 `UrlPatternMatcher` 通配。

### 9.2 硬规则

- **接口自查**：新增或修改接口时，只要请求或响应 payload 含第五节任一类数据，或任何「泄漏后能用来绕过管控」的数据（敏感词库、风控规则、平台红线提示词都算），**必须**在该服务的配置里加入对应忽略清单——这是 Controller 变更的 DoD，backend-reviewer 安全维度必查（禁止事项 #15）
- **逐层各配一次**：同一份敏感数据经过几层服务（网关 / BFF / 业务服务），就要在几层各配一次——**下游配了不代表上游配了**
- **验证也要逐层**：判定"未泄漏"必须看每一层的实际日志，只查一层等于没验
- 判断标准不是"这是不是密码"，而是"这份数据泄漏后能否被用于绕过管控"

### 9.3 发现经过（外部项目，2026-08）

某服务 e2e 时发现敏感词库与提示词正文被完整打进日志；回查发现设计文档早已声明「不入日志」，而实现上一直在打——**声明与实现长期不一致且无人察觉**。根因是把「业务代码不打敏感日志」误当成「敏感数据不入日志」。三周后另一层 BFF 复发同一问题：下游早已配置，上游从未配，且上一轮验证只看了下游日志。
