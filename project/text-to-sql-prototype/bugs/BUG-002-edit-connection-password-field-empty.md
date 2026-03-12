# BUG-002: 编辑连接时密码字段为空

## 基本信息

| 字段 | 内容 |
|------|------|
| **Bug ID** | BUG-002 |
| **模块** | 连接管理 (Connection Module) |
| **页面** | `/connections` |
| **严重级别** | 🟡 Low |
| **优先级** | P2 |
| **发现日期** | 2026-03-13 |
| **发现人** | E2E Tester (Claude Code) |
| **状态** | 🟡 Open |

---

## 问题描述

编辑已有数据库连接时，密码字段显示为空（仅有占位符"请输入密码"），需要重新输入密码才能保存修改。

---

## 复现步骤

1. 访问连接管理页面 `/connections`
2. 确保已存在至少一个数据库连接
3. 点击连接记录右侧的"编辑"按钮
4. 观察编辑弹窗中的密码字段
5. 修改其他字段（如连接名称）
6. 尝试点击"保存修改"按钮

---

## 期望行为

- [ ] 密码字段显示占位符（如 "******"）表示已有密码
- [ ] 提供"保留原密码"选项或复选框
- [ ] 不修改密码时无需重新输入
- [ ] 保存时只更新修改的字段

---

## 实际行为

- [x] 密码字段为空，显示"请输入密码"占位符
- [x] 必须重新输入密码才能保存
- [ ] 无法保留原密码直接保存

---

## 截图

![编辑连接弹窗](../e2e/reports/2026-03-13/screenshots/CONN-007-edit-result.md)

---

## 环境信息

| 项目 | 版本/地址 |
|------|----------|
| 前端 | http://localhost:5173 |
| 后端 | http://localhost:8000 |
| 浏览器 | Playwright Chromium |
| 测试用户 | e2e_tester |

---

## 用户体验影响

1. **操作繁琐**: 用户每次编辑连接都需要重新输入密码
2. **容易出错**: 可能输入错误密码导致连接失败
3. **不符合惯例**: 大多数系统的编辑功能会保留原密码

---

## 建议修复方案

### 方案 1: 前端显示占位符
```vue
<!-- ConnectionEditDialog.vue -->
<el-input
  v-model="form.password"
  type="password"
  placeholder="******"
  show-password
/>
```

### 方案 2: 添加"保留原密码"选项
```vue
<el-checkbox v-model="keepOriginalPassword">
  保留原密码
</el-checkbox>
```

### 方案 3: 后端支持部分更新
```python
# 后端只更新提供的字段，未提供的字段保持不变
if update_data.password:
    connection.password = update_data.password
# 其他字段同理
```

---

## 相关代码

### 前端关键代码位置
```
frontend/src/views/ConnectionView.vue
frontend/src/components/ConnectionEditDialog.vue
```

### 后端关键代码位置
```
backend/app/api/v1/endpoints/connections.py
backend/app/crud/crud_connection.py
backend/app/schemas/connection.py
```

---

## 相关测试用例

| 用例 ID | 描述 | 状态 |
|---------|------|------|
| TC-CONN-007 | 编辑连接信息 | ⚠️ 部分通过 |

---

## 相关文档

- [连接模块测试规范](../e2e/specs/02-Connection-Test-Spec.md)
- [连接模块测试报告](../e2e/reports/2026-03-13/report-02-connection-module.md)

---

## 修复验证清单

修复后需验证以下场景：

- [ ] 编辑连接时密码字段显示占位符
- [ ] 不修改密码可直接保存
- [ ] 修改密码后使用新密码连接成功
- [ ] 保留原密码时连接仍然正常

---

*创建时间: 2026-03-13*
*最后更新: 2026-03-13*
*版本: v1.0*
