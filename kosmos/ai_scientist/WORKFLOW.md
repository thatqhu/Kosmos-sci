# SCI AI Scientist Loop - 工作流程详解

## 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCIResearchWorkflow                           │
│                 (主orchestrator工作流)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├─── 初始化阶段
                              │
                              ├─── 循环迭代阶段 (N个周期)
                              │
                              └─── 最终化阶段
```

---

## 1. 初始化阶段 (`__init__`)

### 组件实例化

```python
SCIResearchWorkflow(
    research_objective="优化SCI重建",
    design_space={...},
    initial_configs=[...],
    anthropic_client=client,
    enable_llm_verification=True
)
```

### 创建的组件

```
┌─────────────────────────────────────────────────────────────────┐
│  SCIResearchWorkflow 实例                                        │
├─────────────────────────────────────────────────────────────────┤
│  1. state_manager: SCIStateManager                              │
│     └─ 管理实验记录、Pareto前沿、上下文                          │
│                                                                   │
│  2. executor: SCIExecutorAgent                                   │
│     └─ 执行单个SCI实验配置                                       │
│                                                                   │
│  3. planner: Planner (✨ NEW - 支持LLM)                          │
│     └─ 生成实验配置提案                                          │
│     └─ 可选：使用Claude API生成智能建议                          │
│                                                                   │
│  4. analysis_agent: AnalysisAgent (✨ NEW - 支持LLM验证)          │
│     └─ Pareto前沿分析                                            │
│     └─ 可选：LLM生成验证算法                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 主循环阶段 (`run`)

### 2.1 种子实验 (可选)

```
如果提供了 initial_configs:
    FOR each config in initial_configs:
        ├─ 创建任务
        ├─ executor.execute(task)
        ├─ 提取 metrics + artifacts
        ├─ 创建 ExperimentRecord
        └─ state_manager.save_sci_experiment(experiment)
```

### 2.2 优化循环

```
FOR cycle in range(1, num_cycles + 1):
    │
    ├─ Step 1: 获取上下文
    │   └─ context = state_manager.get_sci_context(cycle, lookback=3)
    │      返回: {
    │          'explored_configs': [...],  # 已探索配置
    │          'pareto_frontier': [...],   # 当前Pareto前沿
    │          'trends': [...]              # 趋势分析
    │      }
    │
    ├─ Step 2: 规划新实验 (✨ 使用Planner实例)
    │   └─ proposed_configs = _simple_planning(context, num_experiments)
    │       ├─ 构建summary (已探索配置统计)
    │       ├─ planner.planner_step(summary, design_space, budget)
    │       └─ 返回: List[Configuration]
    │
    ├─ Step 3: 执行实验
    │   └─ FOR each config in proposed_configs:
    │       ├─ 创建task
    │       ├─ finding = executor.execute(task, cycle, context)
    │       ├─ 创建ExperimentRecord
    │       └─ state_manager.save_sci_experiment(experiment)
    │
    ├─ Step 4: Pareto分析 (✨ 使用AnalysisAgent实例)
    │   └─ pareto_ids, trends = _analyze_pareto(cycle_experiments)
    │       ├─ 构建WorldModel
    │       ├─ analysis_agent.analysis_step(world_model)
    │       └─ state_manager.update_pareto_frontier(pareto_ids)
    │
    ├─ Step 5: 生成周期总结
    │   └─ state_manager.generate_cycle_summary(cycle)
    │
    └─ 预算检查
        └─ IF experiments_conducted >= budget_max: BREAK
```

---

## 3. 详细流程图

### 3.1 规划阶段 (`_simple_planning`)

```
输入: context, num_experiments
    │
    ├─ 1. 提取已探索配置
    │   └─ explored_configs = context['explored_configs']
    │
    ├─ 2. 构建统计summary
    │   └─ {
    │       'total_experiments': count,
    │       'recon_families': {family: count},
    │       'uq_schemes': {scheme: count},
    │       'frontiers': [],
    │       'constraints': {...}
    │   }
    │
    ├─ 3. 调用Planner
    │   └─ planner.planner_step(summary, design_space, budget)
    │       │
    │       ├─ [如果有LLM客户端]
    │       │   ├─ 识别未探索区域
    │       │   ├─ 构建提示
    │       │   ├─ llm_generate_configs(prompt)
    │       │   │   ├─ 调用Claude API
    │       │   │   └─ 解析JSON响应
    │       │   └─ 返回配置列表
    │       │
    │       └─ [否则]
    │           └─ 返回模拟配置
    │
    └─ 输出: List[Configuration]
```

### 3.2 执行阶段

```
输入: Configuration
    │
    ├─ 1. 创建任务
    │   └─ task = {
    │       'task_id': i,
    │       'description': f"{config.recon_family} + {config.uq_scheme}",
    │       'metadata': {'sci_config': config.to_dict()}
    │   }
    │
    ├─ 2. 执行实验
    │   └─ executor.execute(task, cycle, context)
    │       └─ [实际的SCI重建实验]
    │           返回: {
    │               'finding_id': str,
    │               'statistics': {'psnr': float, 'coverage': float, ...},
    │               'metadata': {'artifacts': {...}}
    │           }
    │
    ├─ 3. 提取结果
    │   ├─ metrics = _extract_metrics(finding)
    │   └─ artifacts = _extract_artifacts(finding)
    │
    ├─ 4. 创建记录
    │   └─ ExperimentRecord(id, config, metrics, artifacts)
    │
    └─ 5. 保存
        └─ state_manager.save_sci_experiment(cycle, experiment)
```

### 3.3 分析阶段 (`_analyze_pareto`)

```
输入: List[ExperimentRecord]
    │
    ├─ 1. 构建WorldModel
    │   └─ world_model = WorldModel()
    │       world_model.experiments = experiments
    │
    ├─ 2. 运行分析
    │   └─ analysis_agent.analysis_step(world_model)
    │       │
    │       ├─ [标准算法]
    │       │   ├─ 按stratum分组 (recon_family × uq_scheme)
    │       │   ├─ FOR each stratum:
    │       │   │   ├─ compute_pareto_front(experiments, objectives)
    │       │   │   │   └─ 识别非支配配置
    │       │   │   ├─ compute_calibration_stats(experiments)
    │       │   │   └─ summarize_trends(experiments, pareto_ids)
    │       │   └─ 合并所有stratum的Pareto集
    │       │
    │       └─ [可选: LLM验证算法]
    │           ├─ generate_verification_algorithm(task, context)
    │           │   └─ 调用Claude生成Python代码
    │           ├─ execute_verification_code(code, experiments)
    │           │   └─ 在沙盒环境中执行
    │           └─ 返回验证结果
    │
    ├─ 3. 更新Pareto前沿
    │   └─ state_manager.update_pareto_frontier(pareto_ids)
    │
    └─ 输出: (pareto_ids, trends)
```

---

## 4. 数据流

```
┌──────────────┐
│ 设计空间      │
│ + 种子配置   │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│            SCIResearchWorkflow              │
│                                             │
│  ┌─────────────────────────────────────┐  │
│  │ Cycle 1                              │  │
│  │  Context → Planner → Configs        │  │
│  │  Configs → Executor → Findings      │  │
│  │  Findings → Analysis → Pareto       │  │
│  └──────────────┬──────────────────────┘  │
│                 │                          │
│  ┌──────────────▼──────────────────────┐  │
│  │ Cycle 2                              │  │
│  │  Context (包含Cycle 1结果)          │  │
│  │  → Planner → ...                    │  │
│  └──────────────┬──────────────────────┘  │
│                 │                          │
│                ...                         │
│                 │                          │
│  ┌──────────────▼──────────────────────┐  │
│  │ Cycle N                              │  │
│  │  → 最终Pareto前沿                    │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
       │
       ▼
┌───────────────────────┐
│ 最终结果              │
│ - Pareto配置          │
│ - 最优配置            │
│ - 性能指标            │
│ - 优化历史            │
└───────────────────────┘
```

---

## 5. 关键组件职责

### 5.1 SCIStateManager
```
职责：
- 保存实验记录到磁盘/数据库
- 维护Pareto前沿
- 提供周期上下文（已探索配置、趋势等）
- 生成周期总结

方法：
- get_sci_context(cycle, lookback)
- save_sci_experiment(cycle, experiment)
- update_pareto_frontier(pareto_ids)
- get_all_findings()
- get_pareto_frontier()
```

### 5.2 Planner (✨ 已增强)
```
职责：
- 分析已探索的配置空间
- 识别未探索区域
- 生成新的实验配置提案
- (可选) 使用LLM智能规划

方法：
- __init__(anthropic_client, api_key, model)  # 新增
- planner_step(summary, design_space, budget)  # 实例方法
- llm_generate_configs(prompt)  # 新增 - LLM调用
- summarize_world_model(world_model)
- identify_underexplored_regions(summary)
```

### 5.3 AnalysisAgent (✨ 已增强)
```
职责：
- 计算Pareto前沿
- 计算校准统计
- 总结趋势
- (可选) LLM生成验证算法

方法：
- __init__(anthropic_client, api_key, enable_llm_verification)  # 新增
- analysis_step(world_model)  # 实例方法
- compute_pareto_front(experiments, objectives)
- compute_calibration_stats(experiments)
- summarize_trends(experiments, pareto_ids, calib_stats)
- generate_verification_algorithm(task, context)  # 新增
- execute_verification_code(code, experiments)  # 新增
- verify_pareto_with_llm(experiments, objectives)  # 新增
```

### 5.4 SCIExecutorAgent
```
职责：
- 执行单个SCI实验配置
- 运行训练、评估流程
- 返回性能指标和artifacts

方法：
- execute(task, cycle, context)
  输入: {
      'task_id': int,
      'description': str,
      'metadata': {'sci_config': dict}
  }
  输出: {
      'finding_id': str,
      'statistics': {psnr, coverage, latency, ...},
      'metadata': {artifacts: {...}}
  }
```

---

## 6. Kosmos集成接口 (✨ 新增)

为未来集成准备的统一接口：

```python
# 1. 获取周期上下文（与ResearchWorkflow兼容）
context = workflow.get_cycle_context(cycle=5, lookback=3)

# 2. 转换为Kosmos Finding格式
finding = workflow.to_research_finding(experiment)
# 返回: {
#   'finding_id': str,
#   'summary': str,
#   'statistics': dict,
#   'evidence_type': 'sci_optimization_result',
#   'metadata': dict
# }

# 3. 批量获取Finding格式
findings = workflow.get_all_findings_as_research_format()

# 4. 获取统计信息
stats = workflow.get_statistics()
# 返回: {
#   'workflow': {...},
#   'state_manager': {...},
#   'planner': {'llm_enabled': bool},
#   'analysis': {'llm_verification_enabled': bool}
# }

# 5. 生成报告
report = await workflow.generate_report()  # Markdown格式
```

---

## 7. 配置示例

### 完整配置
```python
workflow = SCIResearchWorkflow(
    # 必需参数
    research_objective="优化SCI重建的PSNR和覆盖率",
    design_space={
        'recon_families': ['CIAS-Core', 'CIAS-Core-ELP', 'Baseline-CNN'],
        'uq_schemes': ['Conformal', 'Ensemble', 'None']
    },

    # 可选参数
    initial_configs=[config1, config2],  # 种子配置
    optimization_objectives=['psnr', 'coverage', 'latency'],
    anthropic_client=client,  # 或自动从环境变量读取
    artifacts_dir="./artifacts/sci",
    budget_max=50,
    enable_llm_verification=True  # 启用LLM验证算法
)

# 运行
results = await workflow.run(
    num_cycles=10,
    experiments_per_cycle=5
)
```

---

## 8. 工作流程时序图

```
时间轴 →

Cycle 1:  [获取上下文] → [规划3个配置] → [执行实验] → [Pareto分析] → [保存]
                                    ↓                  ↓
                            Config1, Config2,    Finding1, Finding2,
                            Config3              Finding3
                                                      ↓
                                                 Pareto: {Finding1}

Cycle 2:  [获取上下文*] → [规划3个配置] → [执行实验] → [Pareto分析*] → [保存]
          (包含Cycle1)              ↓                  ↓
                            Config4, Config5,    Finding4, Finding5,
                            Config6              Finding6
                                                      ↓
                                                 Pareto: {Finding1, Finding5}

...

Cycle N:  [获取上下文] → [规划] → [执行] → [Pareto分析] → [最终化]
                                              ↓
                                    最终Pareto前沿: {F1, F5, F8, F12}
                                    最优配置: F12 (PSNR: 38.5dB)
```

---

## 9. 改进总结

### 相比旧版的改进

1. **LLM集成** ✨
   - Planner现在支持Claude API生成智能配置建议
   - AnalysisAgent支持LLM生成自定义验证算法

2. **实例化架构** ✨
   - 所有组件现在是实例而非静态类
   - 支持依赖注入和配置

3. **Kosmos兼容** ✨
   - 添加统一接口方法
   - 数据格式可转换

4. **可扩展性** ✨
   - 清晰的职责分离
   - 易于测试和mock

---

## 10. 使用场景

### 场景1: 基础优化（无LLM）
```python
workflow = SCIResearchWorkflow(
    research_objective="优化SCI",
    design_space=design_space,
    budget_max=30
)
results = await workflow.run(num_cycles=5)
```

### 场景2: LLM增强规划
```python
import os
os.environ["ANTHROPIC_API_KEY"] = "sk-..."

workflow = SCIResearchWorkflow(
    research_objective="优化SCI",
    design_space=design_space,
    budget_max=50,
    enable_llm_verification=False  # 仅Planner使用LLM
)
results = await workflow.run(num_cycles=10)
```

### 场景3: 完全LLM驱动
```python
workflow = SCIResearchWorkflow(
    research_objective="优化SCI",
    design_space=design_space,
    budget_max=50,
    enable_llm_verification=True  # Planner + Analysis都用LLM
)
results = await workflow.run(num_cycles=10)

# LLM会生成验证算法并执行
```

---

完成时间: 2025-12-18
版本: v2.0 (LLM-Enhanced)
