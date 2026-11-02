# yzj-dev-workflow · 标准开发流程（第 2 节，按场景 A / B / C）

> 门禁：进入任一场景前第 0 节编码前置门禁已全部满足；场景 C 必须先做影响面分析、外科手术式修改。

## 2. 标准开发流程（按场景）

### 2.1 场景 A：新项目 / 全新业务域

```
1. 创建业务域包：domain/{业务}/
        ↓ 参考 project-structure
2. 定义 Entity（@Table，继承 CommonEntity）
        ↓
3. 创建 Mapper + 手动编写 TableDef（参考 `tabledef` skill）
   （在 support/TableDefCollect.java 中统一注册）
        ↓
4. 创建 Operate / Query / DTO / VO
        ↓ 参考 model-conventions
5. 编写 Service 接口 + ServiceImpl
        ↓ 参考 service-conventions（命名规约、QueryChain）
6. 如有复杂查询：编写 QueryChain
        ↓ 参考 mybatis（IQueryChain 链式查询）
7. 是否涉及跨业务写操作？
   ├── 是 → 创建 Flow（integration/business/{业务}/）
   │       参考 integration-flow
   └── 否 → 跳过
        ↓
8. 编写 Controller（record 类 + 构造注入）
        ↓ 参考 controller-conventions
9. 如有缓存需求：加 @CacheRead/@CachePut/@CacheEvict
        ↓ 参考 cache
10. 如有 gRPC：在 grpc-api 模块定义 proto，实现 GrpcServiceImpl
        ↓ 参考 grpc
11. 单元测试（命名 / 模板 / 必测场景；金融与权限场景不可省）
        ↓ 参考 testing
12. 自检 + Code Review
        ↓ 参考 reviewer
```

### 2.2 场景 B：旧项目新功能

```
1. 阅读同业务域现有代码，确认命名/风格
        ↓
2. 按场景 A 的步骤执行
        ↓
3. 保持与现有代码的一致性（不引入差异）
```

### 2.3 场景 C：旧项目迭代调整

```
1. 影响面分析（受影响的 Service/Controller/Flow/Mapper/QueryChain）
        ↓
2. 外科手术式修改（只改必要的，不顺手重构）
        ↓
3. 回归测试（覆盖被改动方法的调用链）
        ↓
4. 如涉及接口签名变更：检查 SDK / gRPC stub 是否需要同步
```

---
