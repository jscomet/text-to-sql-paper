# MCP Playwright 工具执行示例

本文档提供使用 MCP Playwright 工具执行 E2E 测试的具体示例。

## 工具清单

| 工具名称 | 用途 |
|---------|------|
| `mcp__playwright__browser_navigate` | 导航到指定 URL |
| `mcp__playwright__browser_type` | 在输入框输入文本 |
| `mcp__playwright__browser_click` | 点击页面元素 |
| `mcp__playwright__browser_snapshot` | 获取页面快照 |
| `mcp__playwright__browser_take_screenshot` | 截图保存 |
| `mcp__playwright__browser_wait_for` | 等待元素或文本 |
| `mcp__playwright__browser_fill_form` | 批量填充表单 |
| `mcp__playwright__browser_select_option` | 选择下拉选项 |
| `mcp__playwright__browser_evaluate` | 执行 JavaScript |

---

## 示例 1: 用户登录流程

### 场景
测试用户正常登录流程

### 对应用例
TC-AUTH-001

### 执行步骤

#### 步骤 1: 访问登录页

```json
{
  "tool": "mcp__playwright__browser_navigate",
  "params": {
    "url": "http://localhost:5173/login"
  }
}
```

**预期结果**: 页面显示登录表单

#### 步骤 2: 截图记录初始状态

```json
{
  "tool": "mcp__playwright__browser_take_screenshot",
  "params": {
    "filename": "TC-AUTH-001-01-login-page.png"
  }
}
```

#### 步骤 3: 输入用户名

首先需要获取用户名输入框的引用，通过 `browser_snapshot` 查看页面结构。

```json
{
  "tool": "mcp__playwright__browser_snapshot",
  "params": {}
}
```

假设返回的 snapshot 中用户名输入框的 ref 为 `input-username`：

```json
{
  "tool": "mcp__playwright__browser_type",
  "params": {
    "element": "用户名输入框",
    "ref": "input-username",
    "text": "testuser"
  }
}
```

#### 步骤 4: 输入密码

```json
{
  "tool": "mcp__playwright__browser_type",
  "params": {
    "element": "密码输入框",
    "ref": "input-password",
    "text": "Test@123"
  }
}
```

#### 步骤 5: 截图记录填写状态

```json
{
  "tool": "mcp__playwright__browser_take_screenshot",
  "params": {
    "filename": "TC-AUTH-001-02-form-filled.png"
  }
}
```

#### 步骤 6: 点击登录按钮

```json
{
  "tool": "mcp__playwright__browser_click",
  "params": {
    "element": "登录按钮",
    "ref": "button-login"
  }
}
```

#### 步骤 7: 等待页面跳转

```json
{
  "tool": "mcp__playwright__browser_wait_for",
  "params": {
    "time": 2
  }
}
```

#### 步骤 8: 验证跳转成功

```json
{
  "tool": "mcp__playwright__browser_wait_for",
  "params": {
    "text": "今日查询"
  }
}
```

#### 步骤 9: 截图记录登录后状态

```json
{
  "tool": "mcp__playwright__browser_take_screenshot",
  "params": {
    "filename": "TC-AUTH-001-03-dashboard.png",
    "fullPage": true
  }
}
```

---

## 示例 2: 创建数据库连接

### 场景
测试创建 MySQL 数据库连接

### 对应用例
TC-CONN-001

### 执行步骤

#### 步骤 1: 访问连接管理页（需先登录）

```json
{
  "tool": "mcp__playwright__browser_navigate",
  "params": {
    "url": "http://localhost:5173/connections"
  }
}
```

#### 步骤 2: 点击新建连接

```json
{
  "tool": "mcp__playwright__browser_click",
  "params": {
    "element": "新建连接按钮",
    "ref": "button-new-connection"
  }
}
```

#### 步骤 3: 等待弹窗出现

```json
{
  "tool": "mcp__playwright__browser_wait_for",
  "params": {
    "text": "新建数据库连接"
  }
}
```

#### 步骤 4: 批量填充表单

```json
{
  "tool": "mcp__playwright__browser_fill_form",
  "params": {
    "fields": [
      {
        "name": "连接名称",
        "type": "textbox",
        "ref": "input-name",
        "value": "MySQL-Test"
      },
      {
        "name": "主机地址",
        "type": "textbox",
        "ref": "input-host",
        "value": "localhost"
      },
      {
        "name": "端口",
        "type": "textbox",
        "ref": "input-port",
        "value": "3306"
      },
      {
        "name": "数据库名",
        "type": "textbox",
        "ref": "input-database",
        "value": "test_db"
      },
      {
        "name": "用户名",
        "type": "textbox",
        "ref": "input-username",
        "value": "root"
      },
      {
        "name": "密码",
        "type": "textbox",
        "ref": "input-password",
        "value": "root"
      }
    ]
  }
}
```

#### 步骤 5: 选择数据库类型

```json
{
  "tool": "mcp__playwright__browser_select_option",
  "params": {
    "element": "数据库类型下拉框",
    "ref": "select-type",
    "values": ["mysql"]
  }
}
```

#### 步骤 6: 截图记录表单填写

```json
{
  "tool": "mcp__playwright__browser_take_screenshot",
  "params": {
    "filename": "TC-CONN-001-02-form-filled.png"
  }
}
```

#### 步骤 7: 点击测试连接

```json
{
  "tool": "mcp__playwright__browser_click",
  "params": {
    "element": "测试连接按钮",
    "ref": "button-test-connection"
  }
}
```

#### 步骤 8: 等待测试结果

```json
{
  "tool": "mcp__playwright__browser_wait_for",
  "params": {
    "text": "连接成功",
    "time": 5
  }
}
```

#### 步骤 9: 截图记录测试结果

```json
{
  "tool": "mcp__playwright__browser_take_screenshot",
  "params": {
    "filename": "TC-CONN-001-03-test-success.png"
  }
}
```

#### 步骤 10: 点击保存

```json
{
  "tool": "mcp__playwright__browser_click",
  "params": {
    "element": "保存按钮",
    "ref": "button-save"
  }
}
```

#### 步骤 11: 验证连接出现在列表

```json
{
  "tool": "mcp__playwright__browser_wait_for",
  "params": {
    "text": "MySQL-Test"
  }
}
```

#### 步骤 12: 截图记录连接列表

```json
{
  "tool": "mcp__playwright__browser_take_screenshot",
  "params": {
    "filename": "TC-CONN-001-04-connection-list.png",
    "fullPage": true
  }
}
```

---

## 示例 3: 执行自然语言查询

### 场景
测试自然语言转 SQL 并执行

### 对应用例
TC-QUERY-004

### 执行步骤

#### 步骤 1: 访问查询页并选择数据库

```json
{
  "tool": "mcp__playwright__browser_navigate",
  "params": {
    "url": "http://localhost:5173/query"
  }
}
```

#### 步骤 2: 选择数据库连接

```json
{
  "tool": "mcp__playwright__browser_select_option",
  "params": {
    "element": "数据库选择器",
    "ref": "select-connection",
    "values": ["MySQL-Test"]
  }
}
```

#### 步骤 3: 等待 Schema 加载

```json
{
  "tool": "mcp__playwright__browser_wait_for",
  "params": {
    "text": "users",
    "time": 3
  }
}
```

#### 步骤 4: 截图记录 Schema

```json
{
  "tool": "mcp__playwright__browser_take_screenshot",
  "params": {
    "filename": "TC-QUERY-004-01-schema-loaded.png"
  }
}
```

#### 步骤 5: 输入自然语言问题

```json
{
  "tool": "mcp__playwright__browser_type",
  "params": {
    "element": "问题输入框",
    "ref": "textarea-question",
    "text": "查询所有用户的姓名和邮箱"
  }
}
```

#### 步骤 6: 点击发送

```json
{
  "tool": "mcp__playwright__browser_click",
  "params": {
    "element": "发送按钮",
    "ref": "button-send"
  }
}
```

#### 步骤 7: 等待 SQL 生成

```json
{
  "tool": "mcp__playwright__browser_wait_for",
  "params": {
    "text": "已为您生成SQL",
    "time": 10
  }
}
```

#### 步骤 8: 截图记录生成的 SQL

```json
{
  "tool": "mcp__playwright__browser_take_screenshot",
  "params": {
    "filename": "TC-QUERY-004-02-sql-generated.png"
  }
}
```

#### 步骤 9: 点击执行

```json
{
  "tool": "mcp__playwright__browser_click",
  "params": {
    "element": "执行按钮",
    "ref": "button-execute"
  }
}
```

#### 步骤 10: 等待结果显示

```json
{
  "tool": "mcp__playwright__browser_wait_for",
  "params": {
    "text": "执行结果",
    "time": 5
  }
}
```

#### 步骤 11: 截图记录查询结果

```json
{
  "tool": "mcp__playwright__browser_take_screenshot",
  "params": {
    "filename": "TC-QUERY-004-03-result.png"
  }
}
```

---

## 示例 4: 获取页面信息进行断言

### 使用 browser_evaluate 获取数据

```json
{
  "tool": "mcp__playwright__browser_evaluate",
  "params": {
    "function": "() => { return document.title; }"
  }
}
```

### 获取元素数量

```json
{
  "tool": "mcp__playwright__browser_evaluate",
  "params": {
    "function": "() => { return document.querySelectorAll('.connection-card').length; }"
  }
}
```

### 获取特定元素文本

```json
{
  "tool": "mcp__playwright__browser_evaluate",
  "params": {
    "element": "成功提示",
    "ref": "alert-success",
    "function": "(element) => { return element.innerText; }"
  }
}
```

---

## 示例 5: 完整的测试用例执行记录格式

```markdown
## TC-AUTH-001: 正常登录流程

**执行时间**: 2026-03-13 10:30:00
**执行人**: test-lead
**结果**: ✅ 通过
**耗时**: 15s

### 执行步骤

| 步骤 | 操作 | 工具 | 参数 | 实际结果 | 截图 |
|------|------|------|------|----------|------|
| 1 | 访问登录页 | browser_navigate | url: http://localhost:5173/login | 页面加载成功，显示登录表单 | TC-AUTH-001-01.png |
| 2 | 输入用户名 | browser_type | ref: input-username, text: testuser | 用户名正确显示 | - |
| 3 | 输入密码 | browser_type | ref: input-password, text: Test@123 | 密码显示为星号 | TC-AUTH-001-02.png |
| 4 | 点击登录 | browser_click | ref: button-login | 按钮显示loading | - |
| 5 | 等待跳转 | browser_wait_for | text: 今日查询 | 成功跳转到首页 | TC-AUTH-001-03.png |

### 验证点

- [x] 登录成功跳转到首页
- [x] URL 变更为 /
- [x] 显示今日查询统计
- [x] 侧边栏显示完整菜单

### 问题记录

无

### 备注

执行顺利，所有验证点通过。
```

---

## 最佳实践

### 1. 截图策略

- 关键步骤必须截图（页面状态变化、操作结果）
- 失败步骤立即截图
- 使用描述性文件名：`TC-{ID}-{序号}-{描述}.png`

### 2. 等待策略

- 网络请求后等待 1-3 秒
- SQL 生成等待 5-15 秒
- 评测执行等待 30-60 秒
- 使用 `wait_for` 替代固定等待

### 3. 错误处理

- 工具执行失败记录错误信息
- 失败后尝试截图当前状态
- 根据错误类型决定是否继续

### 4. 数据管理

- 使用 fixtures 中的测试数据
- 避免使用硬编码数据
- 敏感信息使用环境变量

---

## 常见问题

### Q1: 元素找不到

**解决方案**:
1. 先使用 `browser_snapshot` 查看当前页面结构
2. 确认元素是否已加载（使用 `wait_for`）
3. 检查元素是否在 iframe 中

### Q2: 操作太快导致失败

**解决方案**:
1. 在操作间添加适当等待
2. 使用 `wait_for` 等待元素就绪
3. 对于输入操作，可使用 `slowly: true`

### Q3: 弹窗/对话框处理

**解决方案**:
1. 先等待弹窗出现
2. 使用 `wait_for` 确认弹窗文本
3. 再进行弹窗内操作

---

*文档版本: v1.0*
*更新日期: 2026-03-13*
