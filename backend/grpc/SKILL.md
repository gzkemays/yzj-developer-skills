---
name: grpc-development
description: gRPC 服务开发流程与规范指南。当用户需要创建新的 gRPC 接口、开发 gRPC 服务、实现 proto 文件、编写 GrpcServiceImpl 时使用此 skill。包含 proto 文件编写规范、服务端实现规范、调用方使用示例等。
---

# gRPC 服务开发流程与规范指南

本文档描述如何在项目中提供 gRPC 接口，供其他内部服务调用。

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          外部网络                                │
│   外部客户端 ──────── HTTPS :8080 ──────► Spring Security 鉴权  │
│                                                                 │
│   [防火墙 / Docker Network / K8s NetworkPolicy 拦截 :9090]       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                          内部网络                                 │
│                                                                  │
│   其他内部服务 ─── gRPC :9090（无鉴权）──► 目标服务               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**核心原则：**
- HTTP 端口（`8080`）受 Spring Security 保护，对外暴露
- gRPC 端口（`9090`）独立于 HTTP，天然不经过 Spring Security Filter Chain
- **不需要在代码层做鉴权**，安全性由网络层（防火墙 / Docker / K8s）保证

---

## 二、模块结构

```
{project}/
├── {project}-common/                    # 公共定义（不变）
│
├── {project}-grpc-api/                  # gRPC 契约模块（新增）
│   └── src/main/proto/{业务域}/
│       └── {service_name}.proto         # 服务定义
│   # mvn install 后生成 Java Stub 类到 target/generated-sources/
│
└── {project}-server/                    # 服务模块（新增实现）
    └── interfaces/grpc/service/
        └── {ServiceName}GrpcServiceImpl.java
```

**调用方** 只需引入 `{project}-grpc-api` 依赖即可获得 Stub 类，无需依赖 server 模块。

---

## 三、Maven 依赖配置

### 3.1 grpc-api 模块（服务提供方发布）

```xml
<dependencies>
    <dependency>
        <groupId>io.grpc</groupId>
        <artifactId>grpc-stub</artifactId>
    </dependency>
    <dependency>
        <groupId>io.grpc</groupId>
        <artifactId>grpc-protobuf</artifactId>
    </dependency>
    <dependency>
        <groupId>com.google.protobuf</groupId>
        <artifactId>protobuf-java</artifactId>
    </dependency>
    <dependency>
        <groupId>javax.annotation</groupId>
        <artifactId>javax.annotation-api</artifactId>
        <version>1.3.2</version>
    </dependency>
</dependencies>

<build>
    <extensions>
        <!-- 检测当前操作系统，用于下载对应平台的 protoc 编译器 -->
        <extension>
            <groupId>kr.motd.maven</groupId>
            <artifactId>os-maven-plugin</artifactId>
            <version>1.7.1</version>
        </extension>
    </extensions>
    <plugins>
        <plugin>
            <groupId>org.xolstice.maven.plugins</groupId>
            <artifactId>protobuf-maven-plugin</artifactId>
            <version>0.6.1</version>
            <configuration>
                <protocArtifact>
                    com.google.protobuf:protoc:${protobuf.version}:exe:${os.detected.classifier}
                </protocArtifact>
                <pluginId>grpc-java</pluginId>
                <pluginArtifact>
                    io.grpc:protoc-gen-grpc-java:${grpc.version}:exe:${os.detected.classifier}
                </pluginArtifact>
            </configuration>
            <executions>
                <execution>
                    <goals>
                        <!-- 生成 Message 类 -->
                        <goal>compile</goal>
                        <!-- 生成 gRPC Stub 类 -->
                        <goal>compile-custom</goal>
                    </goals>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```

### 3.2 server 模块（服务端实现）

```xml
<!-- grpc-api：proto 契约 + 生成的 Stub 类 -->
<dependency>
    <groupId>com.yeziji</groupId>
    <artifactId>{project}-grpc-api</artifactId>
    <version>${parent.version}</version>
</dependency>
<!-- grpc-spring-boot-starter：gRPC Server 自动配置 -->
<dependency>
    <groupId>net.devh</groupId>
    <artifactId>grpc-spring-boot-starter</artifactId>
</dependency>
```

### 3.3 调用方（其他内部服务）

```xml
<!-- 引入目标服务的 gRPC 契约模块 -->
<dependency>
    <groupId>com.yeziji</groupId>
    <artifactId>{project}-grpc-api</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</dependency>
<!-- gRPC Spring Boot Starter（客户端） -->
<dependency>
    <groupId>net.devh</groupId>
    <artifactId>grpc-spring-boot-starter</artifactId>
    <version>3.1.0.RELEASE</version>
</dependency>
```

---

## 四、gRPC 端口配置

### 4.1 服务端配置（common/grpc.yml）

```yaml
grpc:
  server:
    port: 9090
```

该配置已通过 `application.yml` 的 `spring.config.import` 导入：

```yaml
spring:
  config:
    import:
      - "optional:classpath:common/grpc.yml"
```

### 4.2 调用方配置（application.yml）

```yaml
grpc:
  client:
    # 服务名，与 @GrpcClient 注解中的名称对应
    {service-name}:
      address: 'static://{host}:9090'  # 替换为实际地址
      negotiation-type: plaintext       # 内网无需 TLS
```

---

## 五、Proto 文件编写规范

### 5.1 文件命名与存放

- `.proto` 文件统一使用 `snake_case` 命名，如 `platform_client_datasource.proto`
- 按**业务域**存放于 `grpc-api` 模块的 `src/main/proto/{业务域}/` 目录下
- 每个 `.proto` 文件只定义**一个 `service`**，及其配套的 `message`

### 5.2 文件头选项（固定模板）

```protobuf
syntax = "proto3";

package {业务域};

option java_package = "com.yeziji.{project}.grpc.{业务域}";
option java_multiple_files = true;
option java_outer_classname = "{业务驼峰}Proto";
```

### 5.3 命名规范

| 元素 | 命名风格 | 示例 |
| --- | --- | --- |
| `message` | `UpperCamelCase` | `PlatformClientDatasourceMessage` |
| 请求 message | `{方法名}Request` | `GetByClientCodeRequest` |
| 响应 message（列表） | `{方法名}Response` | `GetErpTypeListResponse` |
| `service` | `{业务描述}Service` | `PlatformClientDatasourceService` |
| `rpc` 方法 | `UpperCamelCase` | `GetErpTypeList` |
| `message` 字段 | `snake_case` | `client_code`, `primary_key` |
| `enum` 值 | `UPPER_SNAKE_CASE` | `DATA_CENTER`, `ERP_HEADQUARTERS` |

### 5.4 Message 编写规范

- **字段编号不得复用**：删除字段后须用 `reserved` 保留编号，防止反序列化异常
- **无参请求**：使用 `google.protobuf.Empty`，需 `import "google/protobuf/empty.proto"`
- **返回单对象**：直接使用对应的 `message`，不强制包一层 Response
- **返回列表**：包装为带 `repeated` 字段的 Response message
- 字段编号从 `1` 开始，**预留字段**（如密码、敏感数据）使用 `reserved` 跳过编号

### 5.5 注释规范

- 文件级：`service` 上方使用 `/** */` 说明服务用途及调用范围
- `message` 级：每个字段使用 `/** */` 说明字段含义
- `rpc` 方法：使用 `/** */` 说明方法用途，并标注对应的 Java Service 方法

### 5.6 基本类型对照表

| proto3 类型 | Java 类型 | 说明 |
| --- | --- | --- |
| `string` | `String` | UTF-8 字符串 |
| `int32` | `int` | 32 位整数 |
| `int64` | `long` | 64 位整数（对应 Java `Long`） |
| `bool` | `boolean` | 布尔值 |
| `double` | `double` | 双精度浮点 |
| `float` | `float` | 单精度浮点 |
| `bytes` | `ByteString` | 字节数组 |

### 5.7 常用关键字示例

**repeated（列表）**

```protobuf
message GetErpTypeListResponse {
    repeated PlatformClientDatasourceMessage items = 1;
}
```

**enum（枚举）**

```protobuf
enum ClientType {
    CLIENT_TYPE_UNSPECIFIED = 0;  // proto3 枚举首个值必须为 0
    DATA_CENTER = 1;
    ERP_HEADQUARTERS = 2;
}
```

> ⚠️ proto3 枚举的第 0 个值是默认值，必须存在，命名惯例为 `{枚举名}_UNSPECIFIED`。

**import（引入其他 proto）**

```protobuf
import "google/protobuf/empty.proto";                        // 无参请求
import "platform/platform_client_datasource.proto";          // 引用同项目其他 proto
```

**reserved（保留编号/字段名）**

```protobuf
message PlatformClientDatasourceMessage {
    int64 id = 1;
    reserved 6, 7;                 // 保留已删除的字段编号（放于末尾）
    reserved "old_field_name";     // 保留已删除的字段名
}
```

### 5.8 字段编号规则

- 编号范围：`1 ~ 536870911`（不得使用 `19000 ~ 19999`，为 proto 内部保留）
- **编号一旦发布不可更改**，只能新增或 `reserved`
- `1 ~ 15` 编号只占 1 个字节，优先分配给**高频字段**

### 5.9 完整文件结构示例

```protobuf
syntax = "proto3";

package platform;

import "google/protobuf/empty.proto";

option java_package = "com.yeziji.datacenter.grpc.platform";
option java_multiple_files = true;
option java_outer_classname = "PlatformClientDatasourceProto";

/** 平台客户端数据源 */
message PlatformClientDatasourceMessage {
    /** 主键 ID */
    int64 id = 1;
    /** 客户端码 */
    string client_code = 2;
    reserved 3, 4;  // 保留已删除的字段编号（放于末尾）
}

/** 获取 ERP 类型数据源列表响应 */
message GetErpTypeListResponse {
    repeated PlatformClientDatasourceMessage items = 1;
}

/** 根据客户端码查询的请求 */
message GetByClientCodeRequest {
    string client_code = 1;
}

/**
 * 平台客户端数据源 gRPC 接口
 * 提供给内部服务调用，不暴露到外部网络（通过端口隔离实现）
 */
service PlatformClientDatasourceService {
    /**
     * 获取 ERP 类型的平台客户端数据源列表
     * 对应 PlatformClientDatasourceService#getErpTypeList()
     */
    rpc GetErpTypeList(google.protobuf.Empty) returns (GetErpTypeListResponse);

    /**
     * 根据客户端码查询平台客户端数据源
     * 对应 PlatformClientDatasourceService#getByClientCode()
     */
    rpc GetByClientCode(GetByClientCodeRequest) returns (PlatformClientDatasourceMessage);
}
```

---

## 六、GrpcServiceImpl 服务端实现规范

### 6.1 核心要点

- 类上标注 `@GrpcService`，由 `grpc-spring-boot-starter` 自动注册到 gRPC 端口
- 继承 protoc 生成的 `{ServiceName}Grpc.{ServiceName}ImplBase`
- 方法内只做：调用 Service → 转换为 proto Message → 写入 responseObserver
- 禁止在 GrpcServiceImpl 中编写业务逻辑
- Entity 转 proto Message 须提取为私有方法 `convertToProtoMessage`，使用 `DataUtils.setIfNotNull` 进行 null 安全赋值，避免 proto 不允许设置 null 值导致 NPE
- 调用顺序固定：`responseObserver.onNext(...)` → `responseObserver.onCompleted()`

### 6.2 实现类模板

```java
package com.yeziji.{project}.interfaces.grpc.impl;

import com.google.protobuf.Empty;
import com.yeziji.common.exception.ApiException;
import com.yeziji.common.utils.DataUtils;
import com.yeziji.{project}.common.msg.{Project}ErrorMsg;
import com.yeziji.{project}.domain.{业务域}.entity.{EntityName}Entity;
import com.yeziji.{project}.domain.{业务域}.service.{ServiceName}Service;
import com.yeziji.{project}.grpc.{业务域}.*;
import io.grpc.stub.StreamObserver;
import jakarta.annotation.Resource;
import net.devh.boot.grpc.server.service.GrpcService;

import java.util.List;

/**
 * {业务描述} gRPC 接口实现
 *
 * @author hwy
 * @since {yyyy/MM/dd}
 */
@GrpcService
public class {ServiceName}GrpcServiceImpl extends {ServiceName}Grpc.{ServiceName}ImplBase {

    @Resource
    private {ServiceName}Service {serviceName}Service;

    @Override
    public void getErpTypeList(Empty request, StreamObserver<GetErpTypeListResponse> responseObserver) {
        List<{EntityName}Entity> entityList = {serviceName}Service.getErpTypeList();

        List<{MessageName}Message> protoList = entityList.stream()
                .map(this::convertToProtoMessage)
                .toList();

        {ResponseName}Response response = {ResponseName}Response.newBuilder()
                .addAllItems(protoList)
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void getByClientCode(GetByClientCodeRequest request, StreamObserver<{MessageName}Message> responseObserver) {
        {EntityName}Entity entity = {serviceName}Service.getByClientCode(request.getClientCode());
        if (entity == null) {
            responseObserver.onError(new ApiException({Project}ErrorMsg.{ERROR_CODE}));
            return;
        }

        responseObserver.onNext(this.convertToProtoMessage(entity));
        responseObserver.onCompleted();
    }

    /**
     * 将实体转换为 proto 消息
     *
     * @param entity 实体
     * @return proto 消息
     */
    private {MessageName}Message convertToProtoMessage({EntityName}Entity entity) {
        {MessageName}Message.Builder protoBuilder = {MessageName}Message.newBuilder();

        DataUtils.setIfNotNull(entity.getId(), protoBuilder::setId);
        DataUtils.setIfNotNull(entity.getField1(), protoBuilder::setField1);
        DataUtils.setIfNotNull(entity.getField2(), protoBuilder::setField2);
        // ... 其他字段映射

        return protoBuilder.build();
    }
}
```

### 6.3 与 HTTP Controller 的对比

| 要素 | HTTP Controller | gRPC ServiceImpl |
|------|----------------|-----------------|
| 注解 | `@RestController` | `@GrpcService` |
| 父类 | 无 | `XxxServiceGrpc.XxxServiceImplBase` |
| 入参 | `@RequestBody` / 路径参数 | 生成的 Request 对象 |
| 返回 | `return result` | `responseObserver.onNext(result)` + `onCompleted()` |
| 鉴权 | Spring Security Filter | 无（网络层隔离） |

---

## 七、调用方使用示例

### 7.1 Stub 类型说明

| Stub 类型 | 使用场景 |
|----------|---------|
| `BlockingStub` | 同步调用，阻塞等待响应（最常用） |
| `FutureStub` | 异步调用，返回 `ListenableFuture` |
| `AsyncStub` | 流式调用，使用 `StreamObserver` 回调 |

### 7.2 使用示例

```java
@Service
public class DataSyncService {

    // @GrpcClient 注入阻塞式 Stub，名称与 yml 中的 client 名称对应
    @GrpcClient("{service-name}")
    private {ServiceName}Grpc.{ServiceName}BlockingStub stub;

    public List<{MessageName}Message> getDataList() {
        {ResponseName}Response response = stub.{methodName}(
                {RequestName}Request.newBuilder().build()
        );
        return response.getItemsList();
    }
}
```

---

## 八、新增 gRPC 接口的开发流程

```
1. 在 proto 文件中定义新的 rpc 方法和 message
   （{project}-grpc-api/src/main/proto/{业务域}/）
          │
2. 执行 mvn install -pl {project}-grpc-api
   → 生成/更新 Java Stub 类
          │
3. 在 server 模块的对应 XxxGrpcServiceImpl 中 override 新方法
   （interfaces/grpc/service/）
          │
4. 调用方刷新 grpc-api 依赖版本后即可使用新接口
```

---

## 九、部署隔离配置

gRPC 端口（9090）仅需在网络层限制外部访问，**无需修改应用代码**。

### 9.1 Docker Compose

```yaml
services:
  datacenter:
    image: {project}-server:latest
    ports:
      - "8080:8080"    # HTTP 对外暴露
      # 9090 不配置 ports 映射 → gRPC 端口不对宿主机暴露
    networks:
      - internal-net   # 其他内部服务通过此内网直接访问 9090

  other-service:
    image: other-service:latest
    networks:
      - internal-net

networks:
  internal-net:
    driver: bridge
```

### 9.2 Kubernetes NetworkPolicy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: grpc-internal-only
spec:
  podSelector:
    matchLabels:
      app: {project}-server
  ingress:
    # HTTP 端口：允许所有来源（由 Ingress/LB 管控）
    - ports:
        - port: 8080
    # gRPC 端口：仅允许同 namespace 内的 Pod 访问
    - ports:
        - port: 9090
      from:
        - podSelector: {}   # namespace 内所有 Pod
```

### 9.3 裸机 / VM（iptables）

```bash
# 封锁来自外网的 9090 访问，仅允许内网 IP 段（如 10.0.0.0/8）
iptables -A INPUT -p tcp --dport 9090 ! -s 10.0.0.0/8 -j DROP
```

---

## 十、常见问题解答

### Q1: gRPC 端口会被 Spring Security 拦截吗？

不会。Spring Security 基于 Servlet Filter Chain，只拦截 HTTP 请求。gRPC 使用独立的 Netty 服务器监听 9090 端口，完全绕过 Spring Security。

### Q2: 如何验证 gRPC 服务是否正常启动？

启动日志中会出现：

```
gRPC Server started, listening on port 9090
```

也可以使用 [grpcurl](https://github.com/fullstorydev/grpcurl) 工具测试：

```bash
grpcurl -plaintext localhost:9090 list
grpcurl -plaintext localhost:9090 {package}.{ServiceName}/{MethodName}
```

### Q3: proto 文件修改后调用方需要重新打包吗？

需要。`grpc-api` 模块是契约，调用方需更新对应版本的依赖。建议遵循语义化版本规范，向后不兼容的变更（如删除字段、修改字段编号）需升级主版本号。

### Q4: proto3 与 proto2 的关键区别是什么？

| 特性 | proto3 | proto2 |
| --- | --- | --- |
| 默认值 | 所有字段有默认值（数字为 `0`，字符串为 `""`，bool 为 `false`） | 可区分"未设置"与"设置为默认值" |
| `required` | 不支持 | 支持 |
| `optional` | 所有字段隐式 optional | 需显式声明 |

> ⚠️ **重要**：proto3 无法区分字段"未赋值"和"赋值为默认值（0 / 空字符串）"。如果业务上需要区分，应使用 `google.protobuf.Int64Value` 等包装类型，或在业务逻辑层另行约定。

### Q5: 字段编号可以重复使用吗？

不可以。**字段编号不得复用**，删除字段后须用 `reserved` 保留编号，防止反序列化异常。编号一旦发布不可更改，只能新增或 reserved。

### Q6: 可以在一个 proto 文件中定义多个 service 吗？

禁止。一个 `.proto` 文件只定义**一个 `service`**。

---

## 十一、禁止事项

- 禁止在 `rpc` 入参/出参括号内留空 `()`，必须声明 message 类型
- 禁止直接使用基本类型（`string`、`int64` 等）作为 `rpc` 参数
- 禁止字段编号跳跃（除非有 `reserved` 说明）
- 禁止一个 `.proto` 文件定义多个 `service`
- 禁止删除已发布的字段而不添加 `reserved`
- 禁止在 proto 中定义与 Java 业务无关的枚举（枚举应以 Java 的 `CommonEnum` 为准，proto 枚举仅用于传输层需要时）
- 禁止在 GrpcServiceImpl 中直接调用 `builder.setXxx(null)`，必须使用 `DataUtils.setIfNotNull` 进行 null 安全赋值
