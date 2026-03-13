# 高级推理功能 E2E 测试报告索引

## 测试规范文档

- [08-Advanced-Inference-Test-Spec.md](../../specs/08-Advanced-Inference-Test-Spec.md) - 高级推理功能 E2E 测试规范
- [09-Performance-Test-Spec.md](../../specs/09-Performance-Test-Spec.md) - 性能测试规范

## 测试报告模板

### 功能测试报告

| 用例 ID | 用例名称 | 模板 | 状态 |
|---------|----------|------|------|
| TC-ADV-001 | vote@k 推理流程 | [TC-ADV-001-report-template.md](./TC-ADV-001-report-template.md) | 待执行 |
| TC-ADV-002 | pass@k 推理流程 | [TC-ADV-002-report-template.md](./TC-ADV-002-report-template.md) | 待执行 |
| TC-ADV-003 | Check-Correct 推理流程 | [TC-ADV-003-report-template.md](./TC-ADV-003-report-template.md) | 待执行 |
| TC-ADV-004 | 推理模式切换测试 | [TC-ADV-004-report-template.md](./TC-ADV-004-report-template.md) | 待执行 |
| TC-ADV-005 | K 值边界测试 | [TC-ADV-005-report-template.md](./TC-ADV-005-report-template.md) | 待执行 |
| TC-ADV-006 | 迭代次数边界测试 | [TC-ADV-006-report-template.md](./TC-ADV-006-report-template.md) | 待执行 |
| TC-ADV-007 | 错误 SQL 修正流程 | [TC-ADV-007-report-template.md](./TC-ADV-007-report-template.md) | 待执行 |
| TC-ADV-008 | 并发任务测试 | [TC-ADV-008-report-template.md](./TC-ADV-008-report-template.md) | 待执行 |
| TC-ADV-009 | WebSocket 进度推送测试 | [TC-ADV-009-report-template.md](./TC-ADV-009-report-template.md) | 待执行 |
| TC-ADV-010 | 超时处理测试 | [TC-ADV-010-report-template.md](./TC-ADV-010-report-template.md) | 待执行 |

### 性能测试报告

| 用例 ID | 用例名称 | 模板 | 状态 |
|---------|----------|------|------|
| TC-PERF-001 ~ 006 | 性能测试综合报告 | [TC-PERF-001-006-report-template.md](./TC-PERF-001-006-report-template.md) | 待执行 |

## 测试执行计划

### 依赖条件

- [ ] WebSocket 实时进度增强 (Task #21)
- [ ] 评测任务配置扩展 (Task #26)
- [ ] SQLChecker 单元测试通过 (Task #22)
- [ ] SQLCorrector 单元测试通过 (Task #23)
- [ ] PassAtKEvaluator 单元测试通过 (Task #25)

### 执行顺序

1. **准备阶段**
   - 确认依赖任务完成
   - 准备测试数据
   - 启动测试环境

2. **功能测试阶段**
   - TC-ADV-001 ~ TC-ADV-003: 核心功能测试
   - TC-ADV-004 ~ TC-ADV-007: 参数和边界测试
   - TC-ADV-008 ~ TC-ADV-010: 高级功能测试

3. **性能测试阶段**
   - TC-PERF-001 ~ TC-PERF-003: 响应时间和并发测试
   - TC-PERF-004 ~ TC-PERF-006: 稳定性和资源测试

4. **回归测试阶段**
   - 执行 07-Regression-Test-Spec.md 中的高级推理回归用例

## 测试数据

### 测试问题集

```javascript
const testQuestions = {
  simple: '查询所有员工',
  moderate: '查询每个部门的平均工资',
  complex: '查询2024年销售额最高的前3个产品及其对应的销售人员',
  errorProne: '查询每个部门的员工数量和总工资，按总工资降序排列'
};
```

### 边界值测试数据

| 参数 | 最小值 | 最大值 | 无效值 |
|------|--------|--------|--------|
| K (candidates) | 1 | 16 | 0, 17 |
| max_iterations | 1 | 5 | 0, 6 |

## 相关文档

- [实施计划](../../../feat/advanced-inference/plan/Implementation-Plan.md)
- [业务逻辑](../../../feat/advanced-inference/Business-Logic.md)
- [API 文档](../../../feat/advanced-inference/API-Documentation.md)
- [回归测试规范](../../specs/07-Regression-Test-Spec.md)

---

*文档版本: v1.0*
*创建日期: 2026-03-13*
*更新日期: 2026-03-13*
