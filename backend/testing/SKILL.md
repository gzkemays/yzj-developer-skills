---
name: testing
description: YZJ 后端单元测试规范。当需要为 Service / Flow / Controller 编写或补齐单元测试、确定测试命名与模板、约定 Mock 边界、覆盖金融与权限高风险场景、或 dev-session P5 后端自测需要可重复执行的验证时使用此 skill。覆盖框架选型（JUnit 5 + Mockito）、命名规则、ServiceImpl / Flow / Controller 测试模板、必测场景、禁止项与覆盖率建议。
---

# YZJ 后端单元测试规范

> 单元测试的目标是**把规则固化成可重复执行的证据**：P5 用例文档里标「AI 可测」的后端用例，优先落成单元测试，而不是手工起服务验证一次就算。
> 金融 / 权限 / 跨域 Flow 的改动，没有对应测试不算"自测通过"。

---

## 一、框架与依赖

| 用途 | 选型 |
|------|------|
| Runner | JUnit 5（Jupiter） |
| Mock | Mockito（`@ExtendWith(MockitoExtension.class)`） |
| 断言 | JUnit `Assertions`；项目已引入 AssertJ 则优先 AssertJ |
| 集成测试（可选） | TestContainers（真实 MySQL / Redis），**只用于集成测试类**，单元测试禁用 |
| 覆盖率 | JaCoCo（门禁按项目入口文件；未定义按第六节建议） |

测试目录与源码镜像：`src/test/java/com/yeziji/{project}/domain/{业务}/service/impl/{Entity}ServiceImplTest.java`。

---

## 二、命名规则（强制）

| 对象 | 规则 | 示例 |
|------|------|------|
| 测试类 | `{被测类}Test` | `OrderServiceImplTest`、`PaymentCreateFlowTest` |
| Mock 字段 | `mock{ClassName}` | `mockOrderMapper`、`mockAccountService` |
| 被测实例 | `{classNameCamel}UnderTest` | `orderServiceImplUnderTest` |
| 测试方法 | `{method}_{scenario}_{expectedResult}` | `add_whenOrderNoExists_throwsApiException` |
| 测试数据构建 | `build{Xxx}()` 私有方法或 `{Xxx}Fixture` | `buildAddOrderOperate()` |

方法名要能**不看方法体就知道测什么**：`testAdd`、`test1`、`addSuccess` 都不合规。

---

## 三、模板

### 3.1 ServiceImpl 单元测试（Mock Mapper / 其他 Service）

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceImplTest {

    @Mock
    private OrderMapper mockOrderMapper;

    @InjectMocks
    private OrderServiceImpl orderServiceImplUnderTest;

    @Test
    void add_success_insertsOnce() {
        // Given
        AddOrderOperate operate = buildAddOrderOperate();
        given(mockOrderMapper.insert(any(OrderEntity.class))).willReturn(1);

        // When
        orderServiceImplUnderTest.add(operate);

        // Then
        verify(mockOrderMapper, times(1)).insert(any(OrderEntity.class));
    }

    @Test
    void add_whenOrderNoExists_throwsApiException() {
        // Given
        AddOrderOperate operate = buildAddOrderOperate();
        given(mockOrderMapper.selectOneByQuery(any())).willReturn(new OrderEntity());

        // When / Then
        ApiException ex = assertThrows(ApiException.class, () -> orderServiceImplUnderTest.add(operate));
        assertEquals(OrderErrorMsg.ORDER_NO_EXISTS.getCode(), ex.getCode());
        verify(mockOrderMapper, never()).insert(any());
    }

    private AddOrderOperate buildAddOrderOperate() {
        return AddOrderOperate.builder().orderNo("O20261024001").amount(new BigDecimal("100.00")).build();
    }
}
```

> MyBatis-Flex `IService` 的默认方法（`queryChain()` / `getById()`）在 `@InjectMocks` 下走不通：Service 内部用 `queryChain()` 的查询，测试时 Mock `Mapper` 的 `selectOneByQuery` / `selectListByQuery`；或把查询抽到独立 QueryChain 类后 `mockStatic`。无法 Mock 的查询改走 3.4 集成测试。

### 3.2 Flow 单元测试（Mock 各 Service，验证编排顺序与失败时的副作用）

```java
@ExtendWith(MockitoExtension.class)
class PaymentCreateFlowTest {

    @Mock private PaymentService mockPaymentService;
    @Mock private AccountService mockAccountService;
    @Mock private LedgerService mockLedgerService;

    @InjectMocks
    private PaymentCreateFlow paymentCreateFlowUnderTest;

    @Test
    void create_success_deductsThenWritesLedger() {
        // Given
        AddPaymentOperate operate = buildOperate();

        // When
        paymentCreateFlowUnderTest.create(operate);

        // Then：顺序断言——扣款在前，流水在后
        InOrder inOrder = inOrder(mockAccountService, mockLedgerService);
        inOrder.verify(mockAccountService).deduct(operate.getAccountId(), operate.getAmount());
        inOrder.verify(mockLedgerService).add(any(AddLedgerOperate.class));
    }

    @Test
    void create_whenDeductFails_neverWritesLedger() {
        // Given
        AddPaymentOperate operate = buildOperate();
        willThrow(new ApiException(AccountErrorMsg.INSUFFICIENT_BALANCE))
                .given(mockAccountService).deduct(any(), any());

        // When / Then
        assertThrows(ApiException.class, () -> paymentCreateFlowUnderTest.create(operate));
        verify(mockLedgerService, never()).add(any());
    }
}
```

### 3.3 Controller 测试（record 构造注入，不起容器）

```java
class AdminOrderV1ControllerTest {

    private final OrderService mockOrderService = mock(OrderService.class);
    private final AdminOrderV1Controller controller = new AdminOrderV1Controller(mockOrderService);

    @Test
    void page_success_wrapsCommonPage() {
        // Given
        given(mockOrderService.getDtoPageByQuery(any())).willReturn(new Page<>());

        // When
        CommonResult<CommonPage<OrderVO>> result = controller.page(new OrderInfoQuery());

        // Then
        assertEquals(CommonStatusCode.SUCCESS, result.getCode());
        assertNotNull(result.getData());
    }
}
```

需要校验 `@Valid`、鉴权注解、路径映射时用 `@WebMvcTest` + `MockMvc`，归入集成测试。

### 3.4 集成测试（真实 DB / Redis，TestContainers）

- 只用于：QueryChain / XML 复杂查询、`@DistributedLock` 行为、事务回滚、多租户条件自动注入
- 类名后缀 `IT`（`OrderQueryChainIT`），与单元测试分开执行（`mvn verify` 阶段）
- 每个测试自备数据、自清理，不依赖执行顺序

---

## 四、必测场景

### 4.1 所有 Service / Flow

- 正常路径（happy path）
- 业务校验失败：对应 `ApiException` 的错误枚举正确、**副作用未发生**（`verify(..., never())`）
- 边界：空列表 / null 入参 / 最大长度 / 分页首尾页

### 4.2 金融 / 资金（`financial` skill 命中时，缺一不算通过）

- 幂等：同一业务单号第二次调用**不重复扣款、不重复插入**，返回首次结果
- 余额不足 / 账户状态异常 → 抛对应异常且无写操作
- 扣减 SQL 返回 0 行（并发失败）→ 抛异常而非静默成功
- 写入失败触发回滚：流水与资金变动要么都有要么都无（集成测试覆盖）
- 金额精度：分摊之和等于总额；`divide` 舍入结果符合业务约定
- 并发扣减（集成测试：多线程同时扣同一账户，终态余额正确、不为负）

### 4.3 权限 / 多租户

- 跨租户 / 跨用户访问被拒（水平越权）
- 手写 SQL 查询结果不含其他租户数据

### 4.4 修复类变更

- P7 失败场景固化为测试（dev-session 回退规则），防同一问题再漏
- `similar-issue-sweep` 扫出的同类位置各补一条

---

## 五、禁止项

| # | 禁止 | 原因 / 替代 |
|---|------|-------------|
| 1 | 单元测试连真实 DB / Redis / 外部 HTTP | 慢且不稳定；Mock 全部外部依赖，真实依赖进集成测试 |
| 2 | 测试方法名无法表达意图（`test1` / `testAdd`） | 按第二节命名 |
| 3 | 一个测试方法堆多个无关断言 | 一个测试验证一个行为 |
| 4 | 为了测试改生产代码可见性（private → public） | 设计有问题就重构，不加 `public`；确需测内部逻辑改为抽类 |
| 5 | 无断言，或只有 `assertNotNull(result)` | 断言具体值、异常类型、`verify` 调用次数 |
| 6 | 测试之间共享可变静态状态、依赖执行顺序 | 每个测试自建数据 |
| 7 | `Thread.sleep` 等待异步 | 把异步入口替换为同步替身，或用 Awaitility |
| 8 | 测试里硬编码真实密钥 / 账号 / 卡号 | 用明显的假数据（支付机构公开的测试卡号除外） |
| 9 | `@SpringBootTest` 跑单元测试 | 整容器启动是集成测试，用 3.1–3.3 模板 |

---

## 六、覆盖率建议

项目入口文件未定义门禁时按此执行；定义了以项目为准：

| 范围 | 建议 |
|------|------|
| Service / Flow 行覆盖 | ≥ 80% |
| 金融 / 权限相关 Service / Flow | ≥ 90%，且第四节 4.2 / 4.3 场景全覆盖 |
| Controller | 以集成测试覆盖路径 + 校验为主，不强求行覆盖 |
| Mapper / QueryChain | 集成测试覆盖，不单测 |

覆盖率是下限不是目标：覆盖到但没断言关键行为的测试不算数。

---

## 七、与 dev-session 的衔接

- **P5**：用例文档里「AI 可测」的后端用例 → 优先落单元测试，并在「执行记录」填测试类与方法名；编译 + 测试命令按项目入口文件
- **P7 不通过**：失败场景先补成测试再修复
- **reviewer**：测试维度核对命名、必测场景、禁止项（见 reviewer 第十四节）
