# pre-dev-alignment · Skill 链路指引

> 门禁：对齐完成后进入编码，按技术栈和任务类型读取对应 skill 主文件全文再动手；前端先搜项目级 skill 与能力登记册。

对齐完成后，按技术栈和任务类型在编码阶段触发对应 skill：

### 后端（backend/）

| 任务类型 | skill |
|----------|-------|
| 确定文件归属 | `project-structure` |
| 创建 DTO/VO/Operate/Query | `model-conventions` |
| Service / QueryChain | `service-conventions` + `mybatis` |
| Controller | `controller-conventions` |
| 跨业务 Flow / Job / Listener / Initializer | `integration-flow` |
| 缓存 / 分布式锁 | `cache` |
| 定时任务 / 调度（@YzjJob） | `job` |
| 鉴权 / Token / OAuth | `security` |
| gRPC | `grpc` |
| TableDef 维护 | `tabledef` |
| DDL 迁移脚本 | `db-migration` |
| 通用工具（CommonResult / SessionContext / ApiException） | `common` |
| 金额 / 余额 / 支付 / 退款 / 结算 / 流水 | `financial` |
| 安全编码红线（持卡人数据 / 密码学 / 注入 / 越权 / SSRF） | `security`（第八节） |
| 单元测试 | `testing` |
| 代码审查 | `reviewer` |

### 前端（frontend/）

| 任务类型 | skill |
|----------|-------|
| CRUD 页面 / 表单弹窗 / 数据表格 | `view-conventions` |
| i18n 补齐 / 硬编码审计 | `i18n-automation` |
| 代码审查 | `reviewer` |
| 项目特有组件/业务模式 | 项目仓库内的项目级 skill（先搜索再开发） |

> 前端原则：先搜项目级 skill 与能力登记册，有则遵循；没有则以同模块现有代码为参考基准。
