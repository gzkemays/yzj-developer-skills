---
name: security
description: yzj-security 安全认证使用指南。当需要配置 JWT/OAuth 认证、使用 SecurityTokenContext 获取 Token 信息、实现 DynamicSecurityAuth 接口、配置 SecurityFilterChain、编写 UserDetailService 实现时使用此 skill。
---

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
