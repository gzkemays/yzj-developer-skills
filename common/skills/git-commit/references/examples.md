# git-commit · 提交信息示例

> 门禁：示例只示意格式；每条 message 仍须通过主文件第三章三分法与铁律 3（无 AI 记号 / 进度词）。

**feat**

```
feat: 新增财务报表的导出接口 & 资金科目模块新增门店维度统计

* 统一导出工具类，支持读库自定义
```

**opt**

```
opt: 数据上报通知由同步改为异步 & 优化批量导入的逻辑

* 批量导入由 for 循环 saveOrUpdate 改为批量 saveOrUpdateBatch
```

**fix**

```
fix: 确认订单当没填写备注时出现 NPE & 商品导出表头没有国际化

* 确认订单要对 remark 字段做空判断
* 商品导出补充 commodity.name, commodity.price 国际化文案
```

**合并（feat + opt + fix）**

```
feat: 新增 XXX

* XXX

opt: 优化 XXX

* XXX

fix: 修复 XXX

* XXX
```

**带 scope（本库 / 反哺）**

```
feat(capability): 反哺 verify-baseline 校验脚本 from YAPD
```

**分支 + 提交配套（修改密码需求）**

```
分支：feat/2026.08.18-edit-password
提交：feat: 新增用户修改密码能力

* 旧密码校验走统一 PasswordEncoder，失败次数计入风控
```

---
