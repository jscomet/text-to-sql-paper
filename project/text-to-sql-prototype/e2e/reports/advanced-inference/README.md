# 高级推理功能 E2E 测试 - 准备文档

## 任务概述

本目录包含高级推理功能的 E2E 测试规范和报告模板。

## 已完成工作

### 1. 测试规范文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 高级推理测试规范 | `../../specs/08-Advanced-Inference-Test-Spec.md` | 10个功能测试用例 |
| 性能测试规范 | `../../specs/09-Performance-Test-Spec.md` | 6个性能测试用例 |

### 2. 测试报告模板

#### 功能测试报告 (TC-ADV-001 ~ TC-ADV-010)

- `TC-ADV-001-report-template.md` - vote@k 推理流程
- `TC-ADV-002-report-template.md` - pass@k 推理流程
- `TC-ADV-003-report-template.md` - Check-Correct 推理流程
- `TC-ADV-004-report-template.md` - 推理模式切换测试
- `TC-ADV-005-report-template.md` - K 值边界测试
- `TC-ADV-006-report-template.md` - 迭代次数边界测试
- `TC-ADV-007-report-template.md` - 错误 SQL 修正流程
- `TC-ADV-008-report-template.md` - 并发任务测试
- `TC-ADV-009-report-template.md` - WebSocket 进度推送测试
- `TC-ADV-010-report-template.md` - 超时处理测试

#### 性能测试报告

- `TC-PERF-001-006-report-template.md` - 性能测试综合报告

### 3. 更新的回归测试规范

已更新 `../../specs/07-Regression-Test-Spec.md`，添加：
- Advanced Inference P1 级回归测试用例
- 向后兼容性回归测试清单

## 测试用例汇总

### 功能测试 (10个)

| 用例 ID | 名称 | 优先级 | 类型 |
|---------|------|--------|------|
| TC-ADV-001 | vote@k 推理流程 | P0 | 功能测试 |
| TC-ADV-002 | pass@k 推理流程 | P0 | 功能测试 |
| TC-ADV-003 | Check-Correct 推理流程 | P0 | 功能测试 |
| TC-ADV-004 | 推理模式切换测试 | P0 | 功能测试 |
| TC-ADV-005 | K 值边界测试 | P0 | 边界测试 |
| TC-ADV-006 | 迭代次数边界测试 | P0 | 边界测试 |
| TC-ADV-007 | 错误 SQL 修正流程 | P0 | 功能测试 |
| TC-ADV-008 | 并发任务测试 | P1 | 性能测试 |
| TC-ADV-009 | WebSocket 进度推送测试 | P1 | 功能测试 |
| TC-ADV-010 | 超时处理测试 | P1 | 异常测试 |

### 性能测试 (6个)

| 用例 ID | 名称 | 优先级 | 类型 |
|---------|------|--------|------|
| TC-PERF-001 | Pass@K 响应时间测试 | P0 | 性能测试 |
| TC-PERF-002 | Check-Correct 响应时间测试 | P0 | 性能测试 |
| TC-PERF-003 | 并发任务测试 | P0 | 并发测试 |
| TC-PERF-004 | 超时机制测试 | P1 | 异常测试 |
| TC-PERF-005 | 内存使用测试 | P1 | 资源测试 |
| TC-PERF-006 | 稳定性测试 | P1 | 稳定性测试 |

## 依赖任务状态

当前被以下任务阻塞：

- [ ] #21: WebSocket 实时进度增强
- [ ] #23: SQLCorrector 单元测试
- [ ] #26: 评测任务配置扩展

## 下一步工作

当依赖任务完成后，将执行以下工作：

1. **环境准备**
   - 启动前后端服务
   - 准备测试数据
   - 验证测试环境

2. **功能测试执行**
   - 按顺序执行 TC-ADV-001 ~ TC-ADV-010
   - 记录测试结果和截图
   - 报告发现的问题

3. **性能测试执行**
   - 执行性能基准测试
   - 记录响应时间和资源使用
   - 验证性能指标

4. **回归测试执行**
   - 执行更新后的回归测试套件
   - 验证向后兼容性
   - 生成回归测试报告

## 相关链接

- [测试报告索引](./index.md)
- [实施计划](../../../feat/advanced-inference/plan/Implementation-Plan.md)
- [E2E 测试总计划](../../specs/00-E2E-Master-Plan.md)

---

*文档版本: v1.0*
*创建日期: 2026-03-13*
