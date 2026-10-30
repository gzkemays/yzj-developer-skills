# yzj-dev-workflow · 关键命名规范与通用模式速查（第 3、4 节）

> 门禁：速查只是入口，详细规范以对应 backend skill 为准（`model-conventions` / `service-conventions` / `controller-conventions` / `common`）；禁止自行创建 Page 类、禁止直抛 RuntimeException。

## 3. 关键命名规范速查

> 详细规范请读取对应 backend skill。

### 3.1 类命名

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| Entity | `{业务}{表名}Entity` | `SystemPermissionEntity` |
| Mapper | `{业务}{表名}Mapper` | `SystemPermissionMapper` |
| Service | `{业务}{表名}Service` | `SystemPermissionService` |
| ServiceImpl | `{业务}{表名}ServiceImpl` | `SystemPermissionServiceImpl` |
| Operate（增删改入参） | `{操作}{业务}Operate` | `AddUserOperate`、`UpdateUserOperate` |
| Query（查询入参） | `{业务}{描述}Query` | `UserInfoQuery` |
| DTO（数据传输） | `{业务}{描述}DTO` | `UserInfoDTO` |
| VO（视图模型） | `{业务}{描述}VO` | `UserInfoVO` |
| QueryChain | `{业务}{描述}QueryChain` | `CustomerInfoQueryChain` |
| Flow | `{业务描述}Flow` | `AuthLoginFlow` |
| Controller | `{平台}{业务}{版本}Controller` | `AdminAuthV1Controller` |
| ConvertAid | `{业务}{描述}ConvertAid` | `SystemPermissionConvertAid` |
| Enum | `{业务}{描述}Enum` | `SystemPermissionTypeEnum` |
| Initializer | `{描述}Initializer` | `LoadPermissionInitializer` |
| Job | `{描述}Job` | `OrderTimeoutJob` |
| Listener | `{描述}Listener` | `DataMessageConfirmListener` |

### 3.2 Operate 命名规范（与 KPay 同源）

**操作动词在前，业务名在后**：

```
✓ AddUserOperate            ✗ UserAddOperate
✓ UpdateUserOperate         ✗ UserUpdateOperate
✓ RemoveUserOperate         ✗ UserRemoveOperate
```

### 3.3 Service 方法命名

| 操作 | 前缀 | 示例 |
|------|------|------|
| 获取单个 | `get` | `getDtoById()` |
| 获取列表 | `get...List` | `getDtoListByQuery()` |
| 获取分页 | `get...Page` | `getDtoPageByQuery()` |
| 统计 | `statistics` | `statisticsUserCount()` |
| 新增 | `add` | `add(AddUserOperate operate)` |
| 修改 | `update` | `update(UpdateUserOperate operate)` |
| 删除 | `remove` | `removeById(Long id)` |

### 3.4 API 路径规范

```
格式：/{版本}/{平台或应用}/{业务路径}
示例：/v1/admin/auth/login
      /v1/open/db/datasource
      /v2/admin/application/version

平台：admin（管理后台）、open（开放平台）、merchant（商户）等
```

---

## 4. 通用模式速查

### 4.1 响应包装

```java
// 成功（无数据）
return CommonResult.success();

// 成功（带数据）
return CommonResult.success(data);

// 成功（分页）
return CommonResult.successPage(page);  // Page<T> 自动转 CommonPage<T>

// 失败
throw new ApiException(SomeErrorMsg.XXX);  // 优先用 ApiException，不直接 return failed
```

### 4.2 分页查询链路

```
Service 层返回 Page<T>（com.mybatisflex.core.paginate.Page）
   ↓
Controller 层用 CommonResult.successPage(page) 自动转换为 CommonPage<T>
```

**禁止自行创建 Page 类**。

### 4.3 上下文获取

```java
// 获取当前登录用户
Long userId = SessionContext.getUserDetailsAttribute(IUserDetails::getUserId);

// 获取当前租户
Long tenantId = SessionContext.getTenantAttribute(TenantInfo::getTenantId);

// 获取 IP
String ip = SessionContext.getServletInfoAttribute(ServletInfo::getIp);
```

### 4.4 异常处理

```java
// 业务异常统一使用 ApiException
throw new ApiException(UserErrorMsg.USER_NOT_FOUND);

// 禁止
throw new RuntimeException("...");
```

### 4.5 Controller 写法（record + 构造注入）

```java
@RestController
@RequestMapping("/v1/admin/user")
public record AdminUserV1Controller(UserService userService) {

    @PostMapping("/page")
    public CommonResult<CommonPage<UserVO>> page(@RequestBody UserInfoQuery query) {
        return CommonResult.successPage(userService.getDtoPageByQuery(query));
    }
}
```
