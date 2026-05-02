---
name: controller-conventions
description: Controller 层开发规范。当需要编写 Controller（record 类写法）、设计 API 路径（版本+平台分层）、确定接口类型（api/sdk/grpc）、使用 CommonResult 包装响应时使用此 skill。
---

# Controller 层开发规范

---

## 一、Controller 编写规范

### record 类 + 构造注入

使用 JDK record 类替代传统的 class + @Resource 方式：

```java
/**
 * 授权相关接口
 *
 * @author hwy
 * @since 2026/03/01 13:08
 **/
@RestController
@RequestMapping("/v1/admin/auth")
public record AdminAuthV1Controller(AuthLoginFlow authLoginFlow, UserService userService) {

    /** 密码登录 */
    @RequestMapping("/login")
    public CommonResult<Void> login(HttpServletResponse response, @RequestBody PasswordAuth passwordAuth) {
        authLoginFlow.passwordLogin(response, passwordAuth);
        return CommonResult.success();
    }
}
```

**要点**：
- 使用 `record` 声明 Controller，构造参数即为注入的依赖
- 无需 `@Resource` 或 `@Autowired`，Spring 自动通过构造注入
- 保留类注释（功能、@author、@since）

### 职责限定

Controller 只做三件事：
1. **参数校验**（@Valid / @NotNull 等）
2. **调用 Service 或 Flow**
3. **返回 CommonResult 包装的结果**

```java
// ✅ 正确
@GetMapping("/{id}")
public CommonResult<UserDTO> getById(@PathVariable Long id) {
    return CommonResult.success(userService.getDtoById(id));
}

// ✅ 正确：需要分页
@PostMapping("/page")
public CommonResult<CommonPage<UserVO>> page(@RequestBody UserQuery query) {
    return CommonResult.successPage(userService.getDtoPageByQuery(query));
}

// ❌ 错误：Controller 中写业务逻辑
@PostMapping("/register")
public CommonResult<Void> register(@RequestBody RegisterDTO dto) {
    UserEntity user = new UserEntity();
    user.setName(dto.getName());
    userMapper.insert(user);           // 禁止直接操作 Mapper
    roleService.bindRoles(user.getId()); // 禁止跨业务调用
    return CommonResult.success();
}
```

---

## 二、路径分层标准

### 路径格式

```
/{版本}/{平台或应用}/{业务路径}
```

| 层级 | 说明 | 示例 |
|------|------|------|
| 版本 | API 版本号 | `v1`、`v2` |
| 平台或应用 | 调用方标识 | `admin`、`open`、`merchant` |
| 业务路径 | 具体业务 | `auth`、`user`、`order` |

### 实战示例

```
/v1/admin/auth/login          # v1 版本，管理后台，登录
/v1/open/auth/login           # v1 版本，开放平台，登录
/v1/open/db/datasource        # v1 版本，开放平台，数据源管理
/v2/admin/application/version # v2 版本，管理后台，应用版本
```

### 对应的 Controller 包结构

```
interfaces/api/controller/
├── v1/
│   ├── admin/
│   │   └── AdminAuthV1Controller.java
│   └── open/
│       ├── OpenAuthV1Controller.java
│       ├── OpenOauthV1Controller.java
│       ├── db/
│       │   └── OpenDatasourceV1Controller.java
│       └── application/
│           └── OpenApplicationV1Controller.java
├── v2/
│   ├── admin/
│   │   └── application/
│   │       └── AdminApplicationV2Controller.java
│   └── open/
│       └── OpenAuthV2Controller.java
└── BackdoorController.java    # 特殊接口（无版本/平台前缀）
```

### Controller 命名规则

格式：`{平台}{业务}{版本}Controller`

| 示例 | 路径 |
|------|------|
| `AdminAuthV1Controller` | `/v1/admin/auth/` |
| `OpenDatasourceV1Controller` | `/v1/open/db/datasource/` |
| `AdminApplicationV2Controller` | `/v2/admin/application/` |

---

## 三、三类接口区分

| 类型 | 位置 | 协议 | 端口 | 鉴权 |
|------|------|------|------|------|
| `api` | `interfaces/api/controller/` | HTTP | 8080 | 完整鉴权（Token + 权限） |
| `sdk` | `interfaces/sdk/provider/` | HTTP | 8080 | 轻量鉴权（服务间签名/白名单） |
| `grpc` | `interfaces/grpc/impl/` | gRPC | 9090 | 无鉴权，网络层隔离 |

### sdk 接口模式

```java
// client — 接口定义
public interface OrderClient {
    OrderDTO getById(Long id);
}

// provider — 接口实现
@RestController
@RequestMapping("/sdk/order")
public record OrderProvider(OrderService orderService) implements OrderClient {
    @Override
    @GetMapping("/{id}")
    public OrderDTO getById(@PathVariable Long id) {
        return orderService.getDtoById(id);
    }
}
```

---

## 四、CommonResult 响应包装

所有 API 接口返回值统一使用 `CommonResult<T>` 包装：

```java
// 成功（无数据）
return CommonResult.success();

// 成功（带数据）
return CommonResult.success(data);

// 成功（分页）
return CommonResult.successPage(page);

// 失败
return CommonResult.failed(ErrorMsg.XXX);
```

---

## 五、禁止事项

1. Controller 中编写业务逻辑
2. Controller 中直接操作 Mapper
3. Controller 中跨业务调用多个 Service（应通过 Flow）
4. 使用传统 class + @Resource 方式编写 Controller（使用 record 类）
5. API 路径不包含版本号
