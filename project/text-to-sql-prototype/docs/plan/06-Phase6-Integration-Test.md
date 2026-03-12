# 阶段6：集成测试与优化

## 阶段目标
进行全面的测试，包括单元测试、API测试、E2E测试，修复Bug并优化性能。本阶段确保项目质量，为部署做准备。

**预计工期**: 1.5天
**并行度**: 中（前后端测试可并行）

---

## Agent 协作关系

```
tester (Task 6.1)               tester (Task 6.2)               tester (Task 6.3)
    │                               │                               │
    ├── 后端单元测试                 ├── API集成测试                  ├── E2E测试
    ├── 服务层测试                   ├── 认证流程测试                 ├── 登录到查询全流程
    └── 工具函数测试                 └── 错误处理测试                 └── 评测任务流程

frontend-dev (Task 6.4)         backend-dev (Task 6.5)
    │                               │
    ├── 前端单元测试                 ├── 性能优化
    └── 组件测试                     └── Bug修复
```

**依赖关系**:
- Task 6.1、6.2、6.3、6.4 可并行执行
- Task 6.5 依赖测试发现的Bug

---

## 任务分解

### Task 6.1: 后端单元测试
**负责人**: `tester`
**依赖**: 阶段3完成

#### 工作内容

1. **测试环境配置** (`backend/tests/conftest.py`)
   - 配置pytest
   - 创建测试数据库（SQLite内存）
   - 创建测试客户端（TestClient）
   -  fixtures：db_session, client, auth_headers

2. **模型测试** (`backend/tests/test_models.py`)
   - User模型CRUD测试
   - DBConnection模型测试
   - 外键关系测试
   - 索引测试

3. **服务层测试**
   - `test_security.py` - 密码哈希、JWT
   - `test_nl2sql.py` - SQL生成（Mock LLM）
   - `test_sql_executor.py` - SQL执行（使用测试DB）
   - `test_evaluator.py` - 正确性验证算法

4. **API测试** (`backend/tests/test_api/`)
   - `test_auth.py` - 注册、登录、token刷新
   - `test_connections.py` - 连接CRUD
   - `test_queries.py` - 查询生成和执行

#### 检查点
- [ ] 测试覆盖率 > 70%
- [ ] 所有服务层测试通过
- [ ] 关键API测试通过

#### 测试点
```bash
cd backend
pytest --cov=app --cov-report=html
coverage report
```

---

### Task 6.2: API集成测试
**负责人**: `tester`
**依赖**: 阶段3完成

#### 工作内容

1. **完整流程测试**
   ```python
   # 测试场景1：完整查询流程
   1. 注册用户
   2. 登录获取token
   3. 创建数据库连接
   4. 生成SQL
   5. 执行SQL
   6. 查看历史记录

   # 测试场景2：完整评测流程
   1. 创建评测任务
   2. 运行评测（Mock Celery）
   3. 查看进度
   4. 查看结果和统计
   ```

2. **边界情况测试**
   - 空数据库连接
   - 超时SQL执行
   - 错误SQL生成
   - 大结果集处理
   - 并发评测任务

3. **安全测试**
   - SQL注入防护
   - 未授权访问
   - Token过期处理
   - 密码强度验证

#### 检查点
- [ ] 完整流程测试通过
- [ ] 边界情况处理正确
- [ ] 安全测试通过

#### 测试点
```bash
# 运行集成测试
pytest tests/integration/ -v
```

---

### Task 6.3: E2E测试
**负责人**: `tester`
**依赖**: 阶段5完成

#### 工作内容

1. **Playwright配置** (`frontend/e2e/`)
   - 安装 `@playwright/test`
   - 配置测试环境
   - 创建测试fixtures（登录态）

2. **核心流程测试**
   - `login.spec.ts` - 登录流程
   - `query.spec.ts` - 查询流程
     - 选择数据库
     - 输入问题
     - 生成SQL
     - 执行SQL
     - 查看结果
   - `connection.spec.ts` - 连接管理
   - `evaluation.spec.ts` - 评测流程

3. **视觉回归测试**（可选）
   - 关键页面截图对比

#### 检查点
- [ ] 所有E2E测试通过
- [ ] 测试覆盖核心用户流程
- [ ] 测试稳定（非 flaky）

#### 测试点
```bash
cd frontend
npx playwright test
npx playwright show-report
```

---

### Task 6.4: 前端单元测试
**负责人**: `frontend-dev`
**依赖**: 阶段5完成

#### 工作内容

1. **测试配置**
   - 安装 `vitest`, `@vue/test-utils`
   - 配置 `vite.config.ts` 测试环境

2. **组件测试**
   - `DataTable.spec.ts` - 表格渲染、分页、排序
   - `ConnectionForm.spec.ts` - 表单验证、提交
   - `QueryResult.spec.ts` - 结果展示

3. **Store测试**
   - `user.store.spec.ts` - 登录状态管理
   - `query.store.spec.ts` - 查询状态管理

4. **工具函数测试**
   - 日期格式化
   - SQL语法检查
   - 数据转换

#### 检查点
- [ ] 测试覆盖率 > 60%
- [ ] 关键组件测试通过
- [ ] Store测试通过

#### 测试点
```bash
cd frontend
npm run test:unit
coverage report
```

---

### Task 6.5: Bug修复与性能优化
**负责人**: `backend-dev` + `frontend-dev`
**依赖**: Task 6.1-6.4 发现的Bug

#### 工作内容

1. **Bug修复**
   - 按优先级修复Bug（P0 > P1 > P2）
   - 回归测试确保修复不引入新问题

2. **性能优化**
   - 后端：
     - 数据库查询优化（N+1问题）
     - API响应缓存（Redis）
     - 异步任务优化
   - 前端：
     - 组件懒加载
     - 大数据表格虚拟滚动
     - 图片/资源优化

3. **日志与监控**
   - 添加性能监控
   - 错误日志收集
   - 关键操作审计日志

#### 检查点
- [ ] 所有P0 Bug修复
- [ ] 性能测试通过（响应时间<3s）
- [ ] 无内存泄漏

#### 测试点
```bash
# 性能测试
# 使用 k6 或 locust 进行压力测试
locust -f locustfile.py
```

---

## 阶段交付物

| 交付物 | 位置 | 验收标准 |
|--------|------|----------|
| 后端测试 | `backend/tests/` | 覆盖率>70%，全部通过 |
| 前端测试 | `frontend/src/**/*.spec.ts` | 覆盖率>60%，全部通过 |
| E2E测试 | `frontend/e2e/` | 核心流程覆盖，全部通过 |
| Bug修复记录 | `docs/BUGFIX.md` | 所有P0 Bug修复 |
| 性能报告 | `docs/PERFORMANCE.md` | 响应时间达标 |

---

## 阶段检查清单

### 测试检查
- [ ] 后端单元测试覆盖率>70%
- [ ] 前端单元测试覆盖率>60%
- [ ] API集成测试通过
- [ ] E2E测试通过
- [ ] 安全测试通过

### Bug检查
- [ ] 无P0级Bug
- [ ] P1级Bug<5个
- [ ] 所有修复有回归测试

### 性能检查
- [ ] 页面加载<2s
- [ ] SQL生成<3s
- [ ] 列表查询<1s
- [ ] 内存使用正常

---

## 进入下一阶段条件

1. ✅ 所有测试通过
2. ✅ 无P0级Bug
3. ✅ 性能指标达标
4. ✅ 代码通过最终review

---

## 风险与应对

| 风险 | 应对措施 |
|------|----------|
| 测试覆盖不足 | 重点测试核心功能，逐步补充 |
| Bug修复引入新问题 | 强制回归测试 |
| 性能优化难度大 | 使用性能分析工具定位瓶颈 |
| E2E测试不稳定 | 增加重试机制，优化等待策略 |

---

*依赖文档: 所有前期文档*
