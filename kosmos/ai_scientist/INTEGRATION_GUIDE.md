# SCI Research Loop - Kosmos Integration Guide

## 概述

本指南说明 SCI Research Loop 的最新架构改进以及如何为未来的 Kosmos 集成做准备。

## 架构改进

### 1. **LLM 支持集成** ✅

#### Planner 增强
- **位置**: `kosmos/ai_scientist/planner.py`
- **改进**:
  - 添加 `__init__()` 方法支持 Anthropic 客户端初始化
  - `llm_generate_configs()` 从静态方法改为实例方法
  - 真实 LLM API 调用替代硬编码提案
  - 自动从环境变量 `ANTHROPIC_API_KEY` 读取

```python
# 使用示例
planner = Planner(api_key="your-key", model="claude-sonnet-4-5")
configs = planner.llm_generate_configs(prompt)
```

#### AnalysisAgent 增强
- **位置**: `kosmos/ai_scientist/analysis.py`
- **改进**:
  - 添加 `__init__()` 方法支持 LLM 客户端
  - 新增 `generate_verification_algorithm()` - LLM 生成自定义验证代码
  - 新增 `execute_verification_code()` - 安全沙盒执行
  - 新增 `verify_pareto_with_llm()` - LLM 驱动的 Pareto 前沿验证

```python
# 使用示例
analysis = AnalysisAgent(
    api_key="your-key",
    enable_llm_verification=True
)
pareto_set, code = analysis.verify_pareto_with_llm(experiments)
```

### 2. **SCIResearchWorkflow 现代化** ✅

#### 实例化组件
- **位置**: `kosmos/ai_scientist/workflow/sci_research_loop.py`
- **改进**:
  - Planner 和 AnalysisAgent 现在作为实例属性
  - 所有方法使用实例而非静态调用
  - 添加 `enable_llm_verification` 参数

```python
# 初始化
self.planner = Planner(anthropic_client=anthropic_client)
self.analysis_agent = AnalysisAgent(
    anthropic_client=anthropic_client,
    enable_llm_verification=enable_llm_verification
)
```

#### 方法更新
- `_simple_planning()` → 使用 `self.planner.planner_step()`
- `_analyze_pareto()` → 使用 `self.analysis_agent.analysis_step()`

### 3. **Kosmos 集成接口** ✅

添加了以下方法以匹配 `kosmos.workflow.ResearchWorkflow` 接口：

#### `get_cycle_context(cycle, lookback)`
获取周期上下文，与 Kosmos 状态管理兼容。

```python
context = workflow.get_cycle_context(cycle=5, lookback=3)
# 返回: {'explored_configs': [...], 'pareto_frontier': [...]}
```

#### `to_research_finding(experiment)`
将 SCI 实验记录转换为 Kosmos Finding 格式。

```python
finding = workflow.to_research_finding(experiment)
# 返回: {
#   'finding_id': '...',
#   'summary': 'SCI Config: ...',
#   'statistics': {...},
#   'evidence_type': 'sci_optimization_result'
# }
```

#### `get_all_findings_as_research_format()`
获取所有实验的 Kosmos 格式列表。

```python
findings = workflow.get_all_findings_as_research_format()
```

#### `get_statistics()`
获取全面的工作流统计信息。

```python
stats = workflow.get_statistics()
# 返回: {
#   'workflow': {...},
#   'state_manager': {...},
#   'planner': {'llm_enabled': True},
#   'analysis': {'llm_verification_enabled': False}
# }
```

#### `generate_report()`
生成 Markdown 格式的研究报告。

```python
report = await workflow.generate_report()
```

---

## 使用方法

### 基本使用（无 LLM）

```python
import asyncio
from kosmos.ai_scientist.workflow import SCIResearchWorkflow
from kosmos.ai_scientist.supervisor import create_design_space, create_initial_configs

async def main():
    workflow = SCIResearchWorkflow(
        research_objective="优化 SCI 重建",
        design_space=create_design_space(),
        initial_configs=create_initial_configs(),
        budget_max=50
    )

    results = await workflow.run(num_cycles=10, experiments_per_cycle=5)
    print(f"实验总数: {results['total_experiments']}")

asyncio.run(main())
```

### 启用 LLM 功能

```python
import os

# 设置 API key
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

# 创建带 LLM 的工作流
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI 重建",
    design_space=create_design_space(),
    initial_configs=create_initial_configs(),
    budget_max=50,
    enable_llm_verification=True  # 启用 LLM 验证
)

results = await workflow.run(num_cycles=10, experiments_per_cycle=5)
```

### 使用 Kosmos 接口

```python
# 获取统计信息
stats = workflow.get_statistics()
print(f"LLM Enabled: {stats['planner']['llm_enabled']}")

# 转换为 Kosmos Finding 格式
experiments = workflow.state_manager.get_all_findings()
for exp in experiments:
    finding = workflow.to_research_finding(exp)
    print(finding['summary'])

# 生成报告
report = await workflow.generate_report()
print(report)
```

---

## 未来 Kosmos 集成步骤

### 阶段 1: 适配器模式（短期）

创建 `SCIWorkflowAdapter` 将 SCI 工作流适配到 `ResearchWorkflow`：

```python
# kosmos/ai_scientist/workflow/sci_adapter.py

class SCIWorkflowAdapter(ResearchWorkflow):
    """适配器：将 SCI 工作流集成到 Kosmos ResearchWorkflow"""

    def __init__(self, research_objective, design_space, **kwargs):
        super().__init__(research_objective, **kwargs)
        self.sci_workflow = SCIResearchWorkflow(...)

    def _execute_cycle(self, cycle, num_tasks):
        # 使用 SCI 工作流执行
        return self.sci_workflow._execute_cycle(cycle, num_tasks)
```

### 阶段 2: 统一抽象（中期）

抽取 `BaseResearchLoop` 基类：

```python
# kosmos/workflow/base_research_loop.py

class BaseResearchLoop(ABC):
    @abstractmethod
    async def _execute_cycle(self, cycle):
        pass

    @abstractmethod
    async def _finalize(self):
        pass

# 两者都继承
class GeneralResearchWorkflow(BaseResearchLoop): ...
class SCIOptimizationWorkflow(BaseResearchLoop): ...
```

### 阶段 3: 完全融合（长期）

将 SCI 作为 ResearchWorkflow 的一个"研究模式"。

---

## 文件结构

```
kosmos/ai_scientist/
├── planner.py                      ✅ 已更新 - LLM 支持
├── analysis.py                     ✅ 已更新 - LLM 验证
├── workflow/
│   ├── sci_research_loop.py       ✅ 已更新 - 实例化 + 接口
│   └── __init__.py
├── INTEGRATION_GUIDE.md            ✅ 新增 - 本文档
└── ...

examples/
├── sci_workflow_example.py         ✅ 已更新 - 展示新功能
└── llm_verification_demo.py        ✅ 新增 - LLM 验证演示
```

---

## API 兼容性

### 与 Kosmos ResearchWorkflow 的接口对齐

| Kosmos Method | SCI Equivalent | Status |
|---------------|----------------|--------|
| `__init__(research_objective, ...)` | ✅ 兼容 | 完成 |
| `run(num_cycles, tasks_per_cycle)` | ✅ 兼容（参数名不同） | 完成 |
| `get_cycle_context(cycle, lookback)` | ✅ 新增 | 完成 |
| `get_statistics()` | ✅ 新增 | 完成 |
| `generate_report()` | ✅ 新增 | 完成 |
| `_execute_cycle(...)` | ✅ 内部实现 | 完成 |

---

## 依赖关系

### 必需
- `anthropic` (pip install anthropic) - 用于 LLM 功能
- Python 3.8+
- asyncio 支持

### 可选
- `ANTHROPIC_API_KEY` 环境变量 - 启用 LLM 功能

---

## 测试

### 运行基本测试

```bash
# 基本功能（无 LLM）
python examples/sci_workflow_example.py

# LLM 功能演示
export ANTHROPIC_API_KEY=your-key
python examples/llm_verification_demo.py
```

### 验证集成接口

```python
# test_sci_integration.py
from kosmos.ai_scientist.workflow import SCIResearchWorkflow

workflow = SCIResearchWorkflow(...)

# 测试接口存在性
assert hasattr(workflow, 'get_cycle_context')
assert hasattr(workflow, 'to_research_finding')
assert hasattr(workflow, 'get_statistics')
assert hasattr(workflow, 'generate_report')

print("✅ All integration interfaces available")
```

---

## 配置选项

```python
SCIResearchWorkflow(
    research_objective: str,           # 优化目标描述
    design_space: Dict,               # 配置空间定义
    initial_configs: List = None,     # 种子配置
    optimization_objectives: List = ['psnr', 'coverage'],
    anthropic_client = None,          # 预配置的客户端
    artifacts_dir: str = "artifacts/sci",
    budget_max: int = 50,             # 最大实验预算
    enable_llm_verification: bool = False  # LLM 验证开关
)
```

---

## 常见问题

### Q: LLM 功能是否必需？
**A**: 否。如果未设置 `ANTHROPIC_API_KEY`，系统会自动降级到标准算法。

### Q: 如何启用 LLM 验证？
**A**: 设置 `enable_llm_verification=True` 并提供有效的 API key。

### Q: 是否与旧版兼容？
**A**: 是。所有旧代码仍可正常工作，新功能是可选的。

### Q: 如何集成到 Kosmos？
**A**: 使用新增的接口方法（`get_cycle_context`, `to_research_finding` 等）可以无缝桥接。

---

## 下一步

1. ✅ **已完成**: LLM 集成
2. ✅ **已完成**: Kosmos 接口准备
3. 🔨 **待办**: 创建 `SCIWorkflowAdapter`
4. 🔨 **待办**: 添加单元测试
5. 🔨 **待办**: 性能基准测试

---

## 贡献者

- 架构设计与实现: 2025-12-18

## 许可证

遵循 Kosmos 项目许可证。
