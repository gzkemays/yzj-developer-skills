# yzj-security 安全认证

---

## 一、模块概览

| 模块 | 说明 |
|------|------|
| `yzj-security` | 安全核心包，提供 Token 接口、OAuth 授权接口 |
| `yzj-security-spring-boot-starter` | 安全 Starter，自动装配过滤器、CORS、权限管理 |

---

## 二、启用安全认证

```java
// JWT 模式
@EnableYzjJwt
@SpringBootApplication
public class Application { ... }

// OAuth 模式
@EnableYzjOauth
@SpringBootApplication
public class Application { ... }

// 同时启用
@EnableYzjSecurity
@SpringBootApplication
public class Application { ... }
```

---

## 三、核心接口

### IJwtTokenGenerate — JWT Token 生成

```java
public class CustomJwtTokenGenerate implements IJwtTokenGenerate {
    @Override
    public SecurityToken generate(Object claims) { /* 生成 Token */ }

    @Override
    public SecurityToken renewal(String refreshProxyToken) { /* 续期 Token */ }

    @Override
    public SecurityToken copy(String proxyToken) { /* 复制 Token */ }

    @Override
    public boolean isExpired(String token) { /* 判断是否过期 */ }

    @Override
    public void deprecated(SecurityToken securityToken) { /* 弃用 Token */ }
}
```

### OauthAuthorizationService — OAuth 授权服务

```java
// 生成授权码
String code = oauthAuthorizationService.generateCode(clientId, userId, scopes, redirectUri);

// 授权码交换令牌
OauthTokenResponse response = oauthAuthorizationService.exchangeCode(code, clientId, clientSecret, redirectUri);

// 刷新令牌
OauthTokenResponse response = oauthAuthorizationService.refreshToken(refreshToken, clientId, clientSecret);
```

### DynamicSecurityAuth — 动态安全认证

```java
public interface DynamicSecurityAuth {
    TenantInfo getTenantInfo();          // 获取租户信息
    Set<String> getIgnoreUrls();        // 获取免鉴权地址
    Set<String> getPermissionUrls();    // 获取需要权限的地址
}
```

---

## 四、Token 上下文

```java
// 获取当前登录用户信息
SecurityToken token = SecurityTokenContext.get();

// 获取用户 ID
Long userId = SecurityTokenContext.getUserId();

// 获取租户 ID
String tenantId = SecurityTokenContext.getTenantId();
```

---

## 五、配置参数

```yaml
yzj:
  security:
    jwt:
      enabled: true
      secret: your-secret-key
      access-token-validity: 3600       # Access Token 有效期（秒）
      refresh-token-validity: 604800    # Refresh Token 有效期（秒）

    oauth:
      enabled: true
      token-endpoint: /oauth/token
      code-expire-seconds: 300
      authorization-endpoint: /oauth/authorize
```

---

## 六、自动装配组件

框架自动配置：
- JWT 过滤器（JwtFilter）
- 日志过滤器（LoggerFilter）
- CORS 配置
- 动态权限管理器（DynamicAuthorizationManager）
- 认证异常处理（RequestAuthenticationEntryPoint）
- 权限异常处理（RequestAccessDeniedHandler）

---

## 七、实战模式

### SecurityEncoder 配置

```java
@Configuration
public class SecurityEncoderConfiguration {
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

### UserDetailService 实现

```java
@Component
public class AdminSecurityUserDetailServiceImpl implements SecurityUserDetailService {
    @Resource
    private UserService userService;
    @Resource
    private SystemRoleService systemRoleService;

    @Override
    public IUserDetails loadUserByToken(SecurityToken token) {
        // 根据 token 信息查询用户并返回 IUserDetails
    }
}
```

### 登录流程（实战示例）

```java
// 在 integration/business/auth/ 下编写 Flow
@Component
public class AuthLoginFlow {
    @Resource
    private IJwtTokenGenerate iJwtTokenGenerate;
    @Resource
    private PasswordEncoder passwordEncoder;
    @Resource
    private UserService userService;

    public void passwordLogin(HttpServletResponse response, PasswordAuth passwordAuth) {
        UserEntity user = userService.queryChain()
                .where(UserEntity::getUsername).eq(passwordAuth.username())
                .oneOpt().orElseThrow(() -> new ApiException(ErrorMsg.USER_NOT_FOUND));

        if (!passwordEncoder.matches(passwordAuth.password(), user.getPassword())) {
            throw new ApiException(ErrorMsg.USER_NOT_FOUND);
        }

        SecurityToken securityToken = iJwtTokenGenerate.generate(
                JwtInfo.builder()
                        .id(user.getId().toString())
                        .authType(SecurityAuthTypeEnum.PASSWORD.toString())
                        .username(user.getUsername())
                        .build()
        );

        response.setHeader(CommonVariousStrPool.HttpHeaders.AUTHORIZATION, securityToken.getProxyToken());
        response.setHeader(CommonVariousStrPool.HttpHeaders.REFRESH_AUTHORIZATION, securityToken.getProxyRefreshToken());
    }
}
```

---

## 八、安全编码红线（PCI DSS / OWASP，与栈无关）

> 以上七节讲"怎么用 yzj-security"；本节讲**任何代码都不能越过的线**。`pre-dev-alignment` 命中 `auth` `token` `password` `encrypt` `key` `card` `pan` `cvv` `pin` `permission` `role` 等关键词，或 backend-reviewer 走安全维度时，逐条核对。

### 8.1 持卡人数据（PCI DSS）

- **永不存储**：CVV / CVC / CVV2、PIN / PIN Block、磁条完整数据——任何形式（含日志、缓存、临时表、异常消息）
- **PAN（卡号）**：落库必须 `@Encryption`（AES）；日志只允许后 4 位；响应只允许脱敏形式（前 6 + `*` + 后 4）；完整 PAN 禁止出现在任何日志或响应
- **PIN**：只在 HSM / 支付网关侧处理，应用层不接触明文

### 8.2 密码学

| 用途 | 允许 | 禁止 |
|------|------|------|
| 对称加密 | AES-256-GCM / AES-256-CBC（`@Encryption` 策略按项目配置） | DES、3DES、RC4；ECB 模式存敏感业务数据 |
| 非对称 | RSA-2048+、ECDSA P-256+ | RSA < 2048 |
| 密码哈希 | BCrypt（`BCryptPasswordEncoder`，见第七节）、Argon2 | MD5、SHA-1、SHA-256 直接哈希、可逆加密存密码 |
| 完整性 / 摘要 | SHA-256+ | MD5、SHA-1（含文件摘要等"非安全"用途，统一不用） |
| 传输 | TLS 1.2+ | HTTP 明文 |
| 随机数 | `SecureRandom`、`NanoIdUtils`（内部 SecureRandom） | `Math.random()`、`new Random()` 生成 token / 验证码 / 盐 |

- 密钥、盐值、secret 来自配置中心 / 环境变量 / KMS，**禁止硬编码**在代码、`@Encryption(key = "...")` 字面量、测试用例里；`yzj.security.jwt.secret` 同理

### 8.3 注入

- MyBatis XML 一律 `#{}`，**禁止 `${}`**；动态排序字段、动态表名用白名单枚举映射，不接受用户输入的列名
- 禁止 JDBC / `QueryWrapper` 字符串拼接 SQL；QueryChain 的 `.where(...)` 传值不拼 SQL 片段
- 用户输入进响应前转义（XSS）；禁止把用户输入拼进 HTML / JS / 跳转 URL

### 8.4 认证与授权

- Token 必须有过期时间（`access-token-validity` / `refresh-token-validity` 不得为 0 或超长）；刷新 Token 独立存储、可撤销（`IJwtTokenGenerate.deprecated`）；禁止 URL 参数传 Token
- 密码 BCrypt 存储；连续登录失败 N 次锁定（阈值按项目）；登录失败只返回统一错误（第七节示例对"用户不存在"与"密码错误"用同一个 `USER_NOT_FOUND`，就是为了不泄露账号是否存在）
- **水平越权**：操作任何资源前校验归属——租户字段由 `CommonBusinessEntity` + 框架条件自动带，**手写 SQL / XML 必须显式带** `tenant_id` / `user_id` 条件
- **垂直越权**：角色权限在过滤器 / `DynamicAuthorizationManager` 统一校验，Controller 用鉴权注解，Service 不重复也不省略
- 免鉴权地址（`getIgnoreUrls`）新增必须在技术设计文档「契约」章节列出并经开发者确认

### 8.5 SSRF 与外部调用

```java
// ❌ 用户输入直接当 URL
restTemplate.getForObject(request.getCallbackUrl(), String.class);

// ✅ 白名单校验 host，再调用；连接超时 + 读超时必须设置
URI uri = URI.create(callbackUrl);
Asserts.isTruth(ALLOWED_HOSTS.contains(uri.getHost()), PaymentErrorMsg.ILLEGAL_CALLBACK_URL);
```

- 回调 / 通知 / 文件拉取 URL 一律白名单；禁止内网地址、`file://`、重定向跟随到任意 host
- 所有外部 HTTP / RPC 设置连接超时 + 读超时与重试上限，失败走降级或 `warn` 日志，不无限等待

### 8.6 安全日志：必须记录与禁止记录

必须记录（`info` / `warn`，带 IP 与用户 ID）：登录成功 / 失败、Token 创建 / 撤销、访问持卡人数据、权限变更、资金核心操作、认证失败与越权尝试。
禁止出现：PAN、PIN、CVV、密码明文、完整 Token、密钥、TOTP 密钥——并注意**框架 `LoggerFilter` 会打全量请求 / 响应体**，相关接口必须进忽略清单（见 `logging` skill 第九节）。

### 8.7 生产环境禁止项

- `debug=true`、`logging.level.root=DEBUG`
- Actuator 敏感端点（`/actuator/env` `/actuator/heapdump` `/actuator/configprops`）暴露到外网
- API 响应含异常类名、堆栈、SQL、内部路径（全局异常处理器统一返回 `CommonResult.failed`）
- 默认凭证（`admin/admin`）、示例密钥、测试账号
- CORS 通配 `*`（框架 CORS 配置必须白名单域名）
- HTTP 明文、禁用证书校验的 HttpClient

### 8.8 安全自检清单（Review 安全维度逐条过）

```
输入与注入
- [ ] Controller 入参 @Valid / @Validated；长度、范围、文件类型与大小已校验
- [ ] XML 无 ${}；动态排序字段走白名单；无字符串拼接 SQL
认证与授权
- [ ] 每个 Controller 方法有鉴权注解，或在免鉴权清单且已评审
- [ ] 资源操作校验归属（租户 / 用户），手写 SQL 显式带隔离条件
- [ ] Token 有过期；无 URL 传 Token；登录失败统一错误
敏感数据
- [ ] 无 CVV / PIN 存储；PAN 加密存储、日志后 4 位、响应脱敏
- [ ] 手机号 / 身份证 / 卡号响应已脱敏；无硬编码密钥、密码、secret
- [ ] 含敏感 payload 的接口已进 yzj.logger.ignore-request-url / ignore-response-url
密码学
- [ ] 密码 BCrypt / Argon2；无 MD5 / SHA-1；随机数 SecureRandom；加密 AES-256
外部调用
- [ ] 回调 URL 白名单；外部请求有连接 + 读超时
日志与配置
- [ ] 无 System.out / printStackTrace；生产无 debug；Actuator 敏感端点未外露；CORS 白名单；全链路 TLS
```
