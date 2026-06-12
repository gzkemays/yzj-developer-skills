---
name: view-conventions
description: 前端页面开发规范（Vue 3 + Naive UI + TypeScript 技术栈）。当需要创建 CRUD 管理页面、表单弹窗、数据表格、确认对话框，或参考现有页面结构进行开发时使用此 skill。涵盖页面结构、组件使用、API 调用、状态管理、i18n 的统一约定。
---

# 前端页面（View）开发规范

> 本 skill 是团队 Vue 3 技术栈的通用页面规范。项目专有部分（设计系统 token 前缀、统一通知工具名、
> 全局类型定义位置）以项目前端 `CLAUDE.md` 为准；本文示例中以 `notifySuccess`、`var(--{prefix}-*)` 代指。

---

## 一、页面文件结构

```
src/views/{模块}/
├── index.vue            # 主页面
├── components/          # 页面级组件（可选）
│   ├── FormModal.vue
│   └── DetailDrawer.vue
```

---

## 二、script setup 标准结构

每个页面的 `<script setup lang="ts">` 按以下顺序组织：

```typescript
// 1. Vue 核心
import { ref, reactive, computed, onMounted, h } from 'vue';
import { useI18n } from 'vue-i18n';

// 2. Naive UI 组件（按需导入）
import { NCard, NDataTable, NButton, NModal, NForm, NFormItem, NInput } from 'naive-ui';
import type { DataTableColumns, FormInst, FormRules, PaginationProps } from 'naive-ui';

// 3. 业务 API
import { fetchXxxList, fetchCreateXxx, fetchUpdateXxx, fetchDeleteXxx } from '@/service/api/xxx';

// 4. 工具类（通知等）
import { notifySuccess } from '@/utils';

// 5. Hooks
import { useLoading } from '@/hooks';

// 6. 初始化
const { t } = useI18n();
const { loading, startLoading, endLoading } = useLoading();
```

---

## 三、CRUD 管理页面模式

### 3.1 标准 CRUD 页面结构（template）

页面由三层组成：**SearchCard**（综合筛选，可选）→ **数据表格卡片**（含工具栏）→ **弹窗/抽屉**。

```vue
<template>
    <div class="xxx-management">
        <!-- 综合查询卡片（keyword 以外的筛选条件，如 状态/角色/日期范围）-->
        <search-card @search="handleSearch" @reset="handleSearchReset">
            <n-gi>
                <n-form-item :label="$t('common.field.status')">
                    <n-select v-model:value="queryParams.status" :options="statusOptions"
                        :placeholder="$t('common.field.selectPlaceholder')" clearable />
                </n-form-item>
            </n-gi>
            <n-gi>
                <n-form-item :label="$t('common.field.createTime')">
                    <n-date-picker v-model:value="createTimeRange" type="daterange"
                        clearable style="width: 100%" />
                </n-form-item>
            </n-gi>
        </search-card>

        <n-card :bordered="false">
            <!-- 工具栏：keyword + 刷新 InputGroup + 操作按钮 -->
            <div class="toolbar">
                <n-input-group style="width: 300px">
                    <n-input v-model:value="queryParams.keyword"
                        :placeholder="$t('page.xxx.searchPlaceholder')"
                        clearable @keyup.enter="handleSearch" />
                    <n-button @click="fetchData">
                        <template #icon><n-icon><refresh-outline /></n-icon></template>
                    </n-button>
                </n-input-group>
                <n-button type="primary" @click="openCreateModal">{{ $t('page.xxx.createXxx') }}</n-button>
            </div>

            <!-- 数据表格 -->
            <n-data-table :columns="columns" :data="tableData" :loading="loading"
                :pagination="pagination" :row-key="(row) => row.id" remote
                @update:page="handlePageChange" @update:page-size="handlePageSizeChange" />
        </n-card>

        <!-- 新建/编辑弹窗 -->
        <n-modal v-model:show="modalVisible" preset="card"
            :title="isEdit ? $t('page.xxx.edit') : $t('page.xxx.create')"
            style="width: 520px" :mask-closable="false">
            <n-form ref="formRef" :model="formModel" :rules="formRules" label-placement="left" label-width="80">
                <!-- 表单项 -->
            </n-form>
            <template #footer>
                <n-space justify="end">
                    <n-button @click="modalVisible = false">{{ $t('common.action.cancel') }}</n-button>
                    <n-button type="primary" :loading="submitLoading" @click="handleSubmit">
                        {{ $t('common.action.confirm') }}
                    </n-button>
                </n-space>
            </template>
        </n-modal>
    </div>
</template>
```

**SearchCard 使用规则**：

- SearchCard 放在表格卡片**上方**，用于 keyword 以外的筛选条件（角色、状态、邮箱、时间范围等）
- keyword 搜索 + 刷新按钮组成 `NInputGroup`，保留在表格卡片**内部**的 toolbar 行
- 页面没有额外筛选条件时可省略 SearchCard
- SearchCard 内用 `<n-gi>` 包裹每个筛选项，组件自动处理响应式网格布局
- `@reset` 事件中清除所有筛选条件并重新查询
- `NDatePicker type="daterange"` → 提交前转换为 `{ startTime, endTime }`

### 3.2 表格列定义

使用 `computed` + i18n，支持渲染函数：

```typescript
const columns = computed<DataTableColumns<Xxx.ListItem>>(() => [
    { title: t('page.xxx.name'), key: 'name', width: 160 },
    { title: t('page.xxx.status'), key: 'status', width: 100,
        render(row) {
            if (row.status == null) return '-';
            return h(NTag, { type: row.status === 1 ? 'success' : 'default', size: 'small' },
                () => row.status === 1 ? t('page.xxx.enabled') : t('page.xxx.disabled'));
        }
    },
    { title: t('page.xxx.action'), key: 'action', width: 200,
        render(row) {
            return h(NSpace, { size: 'small' }, () => [
                h(NButton, { text: true, type: 'primary', onClick: () => openEditModal(row) },
                    () => t('common.action.edit')),
                h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
                    trigger: () => h(NButton, { text: true, type: 'error' }, () => t('common.action.delete')),
                    default: () => t('page.xxx.deleteConfirm')
                })
            ]);
        }
    }
]);
```

### 3.3 分页

```typescript
const pagination = reactive<PaginationProps>({
    page: 1,
    pageSize: 10,
    itemCount: 0,
    showSizePicker: true,
    pageSizes: [10, 20, 50]
});

function handlePageChange(page: number) {
    pagination.page = page;
    fetchData();
}
function handlePageSizeChange(pageSize: number) {
    pagination.pageSize = pageSize;
    pagination.page = 1;
    fetchData();
}
```

---

## 四、表单操作模式

### 4.1 新建/编辑复用同一 Modal

```typescript
const modalVisible = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInst | null>(null);
const formModel = reactive({ id: 0, name: '', description: '' });

function openCreateModal() {
    isEdit.value = false;
    Object.assign(formModel, { id: 0, name: '', description: '' });
    modalVisible.value = true;
}

function openEditModal(row: Xxx.ListItem) {
    isEdit.value = true;
    Object.assign(formModel, { id: row.id, name: row.name, description: row.description || '' });
    modalVisible.value = true;
}
```

### 4.2 提交处理

```typescript
async function handleSubmit() {
    try {
        await formRef.value?.validate();
    } catch {
        return;
    }
    startSubmitLoading();
    try {
        if (isEdit.value) {
            const res = await fetchUpdateXxx({ id: formModel.id, name: formModel.name });
            if (res.data) {
                notifySuccess(t('page.xxx.updateSuccess'));
                modalVisible.value = false;
                fetchData();
            }
        } else {
            const res = await fetchCreateXxx({ name: formModel.name });
            if (res.data) {
                notifySuccess(t('page.xxx.createSuccess'));
                modalVisible.value = false;
                fetchData();
            }
        }
    } finally {
        endSubmitLoading();
    }
}
```

**表单校验规则必须对齐后端**（`api-contract-checker` 规则 4）：后端 `@Size(min/max)` ↔ `formRules.min/max` + 输入框 `:maxlength`；`@NotBlank` ↔ `required: true`。

### 4.3 删除确认

```typescript
// 方式一：NPopconfirm（表格行内，推荐）
h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
    trigger: () => h(NButton, { text: true, type: 'error' }, () => t('common.action.delete')),
    default: () => t('page.xxx.deleteConfirm')
})

// 方式二：$dialog（独立按钮场景）
window.$dialog?.warning({
    title: t('page.xxx.deleteTitle'),
    content: t('page.xxx.deleteConfirm'),
    positiveText: t('common.action.confirm'),
    negativeText: t('common.action.cancel'),
    async onPositiveClick() {
        const res = await fetchDeleteXxx(id);
        if (res.data) {
            notifySuccess(t('page.xxx.deleteSuccess'));
            fetchData();
        }
    }
});
```

**危险操作**（删除项目级资源等）：红色边框 section + 弹窗 + 关键字段输入确认。

---

## 五、API 调用约定

### 5.1 API 文件结构

```typescript
// src/service/api/xxx.ts
import { request } from '../request';

const URL = {
    LIST: '/v1/xxx/page',
    CREATE: '/v1/xxx',
    UPDATE: '/v1/xxx',
    DELETE: '/v1/xxx'
};

export function fetchXxxList(params: Xxx.Query) {
    return request.post<Api.PageResult<Xxx.ListItem>>(URL.LIST, params);
}

export function fetchCreateXxx(params: Xxx.CreateOperate) {
    return request.post<number>(URL.CREATE, params);   // 创建返回新记录 ID
}

export function fetchUpdateXxx(params: Xxx.UpdateOperate) {
    return request.put<boolean>(URL.UPDATE, params);
}

export function fetchDeleteXxx(id: number) {
    return request.delete<boolean>(`${URL.DELETE}/${id}`);
}
```

### 5.2 API 返回值判断

```typescript
// ✅ 有 data 的接口：用 res.data 判断
const res = await fetchCreateXxx(params);
if (res.data) { notifySuccess(...); }

// ✅ Void 接口（data=null）：用 code 判断
const res = await fetchLogin(params) as Api.Result<null>;
if (res.code === REQUEST_SUCCESS_CODE) { ... }

// ❌ 错误：对 Void 接口用 data 判断
if (res.data) { ... }  // data 是 null，永远为 falsy
```

### 5.3 类型与大字段

- TypeScript 类型必须是后端 VO/Operate 字段的**子集**（`api-contract-checker` 规则 3）
- 雪花 ID 用 `string` 承载，禁止 `Number()` 转换
- 大字段（LONGTEXT，如 contentJson）在 service 层做 `parse/stringify` 转换，组件层只见对象

---

## 六、useLoading Hook

统一的加载状态管理，避免手动操作 boolean：

```typescript
const { loading, startLoading, endLoading } = useLoading();

// 可创建多个独立的 loading 状态
const { loading: submitLoading, startLoading: startSubmit, endLoading: endSubmit } = useLoading();
```

---

## 七、i18n 键命名约定

### 7.1 通用键（跨页面复用，避免重复定义）

```
# 通用操作
common.action.confirm / cancel / save / delete / edit / create
common.action.search / reset / back / submit / expand / collapse / refresh

# 通用字段标签
common.field.status / email / createTime / updateTime / description
common.field.enabled / disabled / selectPlaceholder / inputPlaceholder
```

> **原则**：一个字段标签在 2 个以上页面出现 → 提取到 `common.field.*`；页面特有的保留在 `page.{模块}.*`。

### 7.2 页面特有键

```
page.{模块}.{操作或字段}

page.user.searchPlaceholder / createSuccess / updateSuccess / deleteSuccess / deleteConfirm
page.user.username / nickname    # 仅该页面使用的标签
```

补齐与审计用 `i18n-automation` skill。

---

## 八、CSS BEM 命名

```css
.{模块名} { }                           /* 块 */
.{模块名}__toolbar { }                  /* 元素 */
.{模块名}__toolbar--active { }          /* 修饰符 */
```

- 使用 `<style scoped>`；Naive UI 样式穿透用 `:deep()`
- 颜色/间距/圆角/字体一律用项目设计系统 token（`var(--{prefix}-*)`），**禁止硬编码颜色**

---

## 九、成功提示规范

所有操作成功后使用项目统一通知工具（如 `notifySuccess()`），不直接使用 `window.$message`：

```typescript
import { notifySuccess } from '@/utils';

// ✅ 正确
notifySuccess(t('page.user.createSuccess'));

// ❌ 禁止
window.$message?.success(t('page.user.createSuccess'));
```

---

## 十、数据展示工具（强制）

- `displayText(value)` — 所有文本列必须使用，null/blank → `'-'`
- `formatDateTime(value)` — 所有时间列必须使用，格式 `yyyy-MM-dd HH:mm:ss`
- 枚举/状态列：`if (value == null) return '-'` 后再渲染 NTag
- 从 `@/utils` 导入（或项目约定位置）

---

## 十一、新增 CRUD 页面检查清单

```
- [ ] 页面文件放置在 src/views/{模块}/index.vue
- [ ] 路由已注册，meta 包含 title/icon/order/requiresAuth
- [ ] API 文件 src/service/api/{模块}.ts 已创建（返回类型遵循契约）
- [ ] TypeScript 类型 src/typings/{模块}/ 已定义（后端字段子集）
- [ ] i18n key 已在所有语言文件中补齐
- [ ] 表格列定义使用 computed + i18n；文本/时间列用 displayText / formatDateTime
- [ ] 操作成功使用统一通知工具
- [ ] 删除操作使用 NPopconfirm 确认
- [ ] loading 状态使用 useLoading hook
- [ ] <style scoped> + BEM 命名 + 设计系统 token
- [ ] 表单校验与后端 @Size / @NotBlank 对齐
```
