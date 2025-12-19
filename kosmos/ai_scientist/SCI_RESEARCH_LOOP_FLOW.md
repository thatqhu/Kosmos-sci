# SCI Research Loop 运行流程详解

## 📋 总览

SCI Research Loop 是一个自动化的科学实验优化工作流，专门用于 Snapshot Compressive Imaging (SCI) 重建算法的多目标优化。

**核心特点**：
- ✅ 直接从 LLM 规划开始（跳过种子实验）
- ✅ 多周期迭代优化
- ✅ Pareto 前沿追踪
- ✅ 配置去重
- ✅ 状态持久化

---

## 🏗️ 架构组件

```
SCIResearchWorkflow
├── state_manager (SCIStateManager)      # 状态管理
├── executor (SCIExecutorAgent)          # 实验执行
├── planner (Planner)                    # 配置规划
└── analysis_agent (AnalysisAgent)       # Pareto分析
```

---

## 🔄 完整执行流程

### Phase 0: 初始化 (`__init__`)

```python
workflow = SCIResearchWorkflow(
    research_objective="优化SCI重建算法",
    design_space=design_space,
    initial_configs=None,  # 不运行种子实验
    budget_max=50
)
```

**初始化内容**：

1. **状态管理器**：`SCIStateManager`
   - artifacts目录：`artifacts/sci/`
   - Pareto缓存：`_pareto_cache`
   - 设计空间覆盖：`_design_space_coverage`

2. **执行器**：`SCIExecutorAgent`
   - 包装原始 `Executor.run_campaign()`
   - 输出标准 `Finding` 格式

3. **规划器**：`Planner`
   - LLM驱动配置生成
   - 支持配置去重
   - 探索未覆盖区域

4. **分析代理**：`AnalysisAgent`
   - Pareto前沿计算
   - 趋势总结

---

### Phase 1: 主循环 (`run(num_cycles=10)`)

```python
results = await workflow.run(
    num_cycles=10,
    experiments_per_cycle=5
)
```

**执行流程**：

```
for cycle in 1..10:
    │
    ├─→ Step 1: 获取上下文
    ├─→ Step 2: LLM规划配置
    ├─→ Step 3: 执行实验
    ├─→ Step 4: Pareto分析
    └─→ Step 5: 生成摘要
```

---

## 📊 单周期详细流程 (`_execute_cycle`)

### Step 1: 获取上下文 (lines 198-206)

```python
context = state_manager.get_sci_context(cycle, lookback=3)
```

**上下文内容**：
```python
{
    'cycle': 5,
    'recent_findings': [...],           # 最近3个周期的发现
    'pareto_frontier': ['exp_1', ...],  # Pareto最优ID列表
    'design_space_coverage': {          # 已探索的family统计
        'CIAS-Core': 5,
        'CIAS-Core-ELP': 3
    },
    'explored_configs': [...]           # 所有已运行的配置
}
```

---

### Step 2: LLM规划生成配置 (`_simple_planning`, lines 208-218)

```python
proposed_configs = self._simple_planning(context, num_experiments=5)
```

**规划过程**：

#### 2.1 构建摘要 (Summary)

```python
summary = {
    'total_experiments': len(explored_configs),
    'recon_families': {
        'CIAS-Core': 5,
        'CIAS-Core-ELP': 3,
        'Baseline-CNN': 2
    },
    'uq_schemes': {
        'None': 4,
        'Conformal': 3,
        'Ensemble': 3
    },
    'best_psnr': 29.5,  # 当前最佳
    'avg_psnr': 27.8
}
```

#### 2.2 调用 Planner

```python
configs = self.planner.planner_step(
    summary=summary,
    design_space=design_space,
    budget_remaining=5,
    explored_configs=None  # 可选：传入已探索配置进行去重
)
```

**Planner 内部逻辑**：

```
1. 识别未探索区域 (identify_underexplored_regions)
   └─→ 例如：只测试了2种family，还有5种未测试

2. 构建 LLM 提示 (build_planner_prompt)
   └─→ 包含：gaps、frontiers、constraints、budget

3. LLM 生成配置 (llm_generate_configs)
   ├─→ 如果有 API key：调用 Claude
   └─→ 否则：返回模拟配置

4. 投影到设计空间 (project_to_design_space)
   └─→ 确保所有参数在有效范围内

5. 验证配置 (is_valid_config)
   └─→ 检查约束条件

6. 配置去重 (通过 hash)
   └─→ 过滤已运行的配置

返回：List[Configuration]  # 5个新配置
```

**LLM 提示示例**：

```
You are an AI experiment designer for snapshot compressive imaging (SCI).

Current state:
- Under-explored regions: ['CIAS-Core-Transform', 'CIAS-Core-Hybrid']
- Pareto frontier: 3 configurations
- Best PSNR: 29.5 dB
- Constraints: {'max_latency': 100, 'min_coverage': 0.8}
- Remaining budget: 5 experiments

Propose 5 new experiment configurations, prioritizing under-explored regions.
Each configuration should include: recon_family, uq_scheme, and relevant parameters.

Output as JSON:
{
  "experiments": [
    {
      "recon_family": "CIAS-Core-Transform",
      "recon_params": {...},
      "uq_scheme": "Conformal",
      ...
    },
    ...
  ]
}
```

#### 2.3 返回配置

```python
# 返回示例
[
    Configuration(
        recon_family='CIAS-Core-Transform',
        recon_params={'num_layers': 12},
        uq_scheme='Conformal',
        uq_params={'alpha': 0.1},
        ...
    ),
    # ... 4 more configs
]
```

---

### Step 3: 执行实验 (lines 220-259)

```python
for config in proposed_configs:
    # 3.1 创建任务
    task = {
        'task_id': i,
        'description': f"{config.recon_family} + {config.uq_scheme}",
        'metadata': {
            'sci_config': config.to_dict()
        }
    }

    # 3.2 执行实验
    finding = await self.executor.execute(task, cycle, context)

    # 3.3 创建实验记录
    experiment = ExperimentRecord(
        id=finding['finding_id'],  # 例如: "sci_exp_a3b2c1d4"
        config=config,
        metrics=Metrics(
            psnr=29.8,
            coverage=0.85,
            latency=24.3,
            calibration_error=0.05
        ),
        artifacts=Artifacts(
            checkpoint='path/to/model.pth',
            train_log='path/to/log.txt',
            ...
        )
    )

    # 3.4 保存到状态管理器
    await state_manager.save_sci_experiment(cycle, experiment)
```

**Executor 执行流程** (`SCIExecutorAgent.execute`):

```
1. 提取配置
   config = Configuration(...)

2. 调用原始执行器
   metrics, artifacts = Executor.run_campaign(config)
   └─→ 这里是模拟执行，返回模拟指标

3. 生成 Finding ID
   finding_id = f"sci_exp_{uuid.uuid4().hex[:8]}"

4. 构建 Finding 字典
   {
       'finding_id': 'sci_exp_a3b2c1d4',
       'summary': 'SCI实验: CIAS-Core + Conformal...',
       'statistics': {
           'psnr': 29.8,
           'coverage': 0.85,
           'latency': 24.3,
           ...
       },
       'methods': '使用CIAS-Core架构...',
       'interpretation': '配置达到优秀的重建质量...',
       'evidence_type': 'sci_experiment',
       'metadata': {
           'config': {...},
           'artifacts': {...}
       }
   }

5. 返回 Finding
```

---

### Step 4: Pareto 分析 (lines 261-280)

```python
pareto_ids, trends = self._analyze_pareto(cycle_experiments)
```

**分析流程**：

```python
# 1. 构建 WorldModel
world_model = WorldModel()
world_model.experiments = cycle_experiments  # 本周期的实验

# 2. 调用 AnalysisAgent
pareto_ids, trends = AnalysisAgent.analysis_step(world_model)
```

**AnalysisAgent 逻辑**：

```
1. 按层级分组 (strata)
   strata = {
       ('CIAS-Core', 'None'): [exp1, exp2],
       ('CIAS-Core', 'Conformal'): [exp3, exp4],
       ...
   }

2. 为每个层级计算 Pareto 前沿
   objectives = ['psnr', 'coverage']

   对于每个实验：
   - 检查是否被其他实验支配
   - 支配条件：所有目标 >= 且至少一个目标 >

   返回未被支配的实验 ID

3. 计算校准统计
   {
       'mean_error': 0.05,
       'max_error': 0.08,
       'min_error': 0.02
   }

4. 生成趋势总结
   "Pareto frontier contains 3 configurations.
    Average PSNR: 29.2 dB.
    Best config uses CIAS-Core-ELP, PSNR=29.8 dB.
    Average calibration error: 0.050."

返回：
- pareto_ids: {'sci_exp_a3b2', 'sci_exp_c5d6', ...}
- trends: ["[CIAS-Core × None] ...", "[CIAS-Core-ELP × Conformal] ..."]
```

**更新 Pareto 前沿**：

```python
state_manager.update_pareto_frontier(pareto_ids)
pareto_history.append({
    'cycle': 5,
    'pareto_size': 3,
    'experiments_run': 5
})
```

---

### Step 5: 生成周期摘要 (lines 282-285)

```python
await state_manager.generate_cycle_summary(cycle)
```

**生成内容**：

文件：`artifacts/sci/cycle_5/summary.md`

```markdown
# Cycle 5 Summary

**Date**: 2025-12-19
**Total Findings**: 5
**Validated Findings**: 5
**Validation Rate**: 100.0%

## Key Findings

### Finding 1: SCI配置评估: CIAS-Core-ELP + Conformal

**Statistics**:
- psnr: 29.8000
- coverage: 0.8500
- latency: 24.3000
- calibration_error: 0.0500

**Evidence**: `path/to/train_log.txt`

### Finding 2: ...
```

---

## 📁 文件系统结构

```
artifacts/sci/
├── cycle_0/          # (如果有种子实验)
├── cycle_1/
│   ├── task_1_finding.json
│   ├── task_2_finding.json
│   ├── task_3_finding.json
│   ├── task_4_finding.json
│   ├── task_5_finding.json
│   └── summary.md
├── cycle_2/
│   └── ...
├── cycle_3/
│   └── ...
...
└── cycle_10/
    └── ...
```

**Finding JSON 示例** (`task_1_finding.json`):

```json
{
  "finding_id": "sci_exp_a3b2c1d4",
  "cycle": 5,
  "task_id": 1,
  "summary": "SCI配置评估: CIAS-Core-ELP + Conformal",
  "statistics": {
    "psnr": 29.8,
    "coverage": 0.85,
    "latency": 24.3,
    "calibration_error": 0.05
  },
  "methods": "使用CIAS-Core-ELP架构进行SCI重建，UQ方案: Conformal",
  "interpretation": "优秀的重建质量 (PSNR > 28dB); 高可靠的不确定性估计 (coverage > 90%); 快速推理 (< 20ms)",
  "evidence_type": "sci_optimization_result",
  "metadata": {
    "config": {
      "recon_family": "CIAS-Core-ELP",
      "recon_params": {"num_layers": 10, "hidden_dim": 128},
      "uq_scheme": "Conformal",
      "uq_params": {"alpha": 0.1},
      "train_config": {"epochs": 50, "lr": 0.001},
      "forward_config": {"compression_ratio": 8}
    },
    "artifacts": {
      "checkpoint": "simulated_checkpoint.pth",
      "uq_params": "simulated_uq.json",
      "train_log": "simulated_train.log",
      "eval_samples": "simulated_eval.npz",
      "fig_scripts": "simulated_figs.py"
    },
    "pareto_optimal": true
  },
  "timestamp": "2025-12-19T14:00:00"
}
```

---

## 🎯 最终阶段 (Phase 3: Finalize)

### `_finalize_results()` (lines 393-451)

```python
# 1. 获取所有发现
all_findings = state_manager.get_all_findings()
sci_findings = [f for f in all_findings if f.evidence_type == "sci_optimization_result"]

# 2. 过滤 Pareto 最优
pareto_ids = state_manager.get_pareto_frontier()
pareto_findings = [f for f in sci_findings if f.finding_id in pareto_ids]

# 3. 找出最佳配置 (PSNR最高)
best_finding = max(pareto_findings, key=lambda f: f.statistics['psnr'])

# 4. 返回结果
return {
    'total_experiments': 50,
    'cycles_completed': 10,
    'final_pareto_size': 8,
    'best_configuration': {
        'recon_family': 'CIAS-Core-ELP',
        'uq_scheme': 'Conformal',
        'recon_params': {...}
    },
    'best_metrics': {
        'psnr': 29.8,
        'coverage': 0.85,
        'latency': 24.3
    },
    'pareto_history': [
        {'cycle': 1, 'pareto_size': 2, 'experiments_run': 5},
        {'cycle': 2, 'pareto_size': 4, 'experiments_run': 5},
        ...
    ],
    'total_time': 120.5
}
```

---

## 🔑 关键数据流

```
Cycle N 开始
   │
   ├─→ 上下文检索
   │   ├─ 读取: artifacts/cycle_{N-3..N-1}/*.json
   │   ├─ 读取: state_manager._pareto_cache
   │   └─ 返回: context dict
   │
   ├─→ LLM 规划
   │   ├─ 输入: summary (统计信息)
   │   ├─ LLM调用: Claude API (如果有key)
   │   ├─ 配置去重: 通过 hash
   │   └─ 返回: List[Configuration] (5个)
   │
   ├─→ 实验执行
   │   ├─ for config in proposed_configs:
   │   │   ├─ Executor.run_campaign(config)
   │   │   ├─ 生成 Finding
   │   │   └─ 保存到 artifacts/cycle_N/task_i_finding.json
   │   └─ 返回: List[ExperimentRecord]
   │
   ├─→ Pareto 分析
   │   ├─ 输入: cycle_experiments
   │   ├─ 计算: 多目标优化前沿
   │   ├─ 更新: state_manager._pareto_cache
   │   └─ 返回: (pareto_ids, trends)
   │
   └─→ 生成摘要
       └─ 保存: artifacts/cycle_N/summary.md

Cycle N+1 开始...
```

---

## 💡 关键特性

### 1. **配置去重**

```python
# 通过 Configuration.get_hash_key() 实现
hash_key = config.get_hash_key()
# 生成格式: "family|params|uq|uq_params"

if hash_key in explored_hashes:
    skip  # 跳过重复配置
```

### 2. **Pareto 前沿追踪**

```python
# 多目标优化: 同时优化 PSNR, Coverage, -Latency
# 未被支配 = Pareto最优
# 持久化: state_manager._pareto_cache
```

### 3. **状态持久化**

```python
# 4层架构:
# Layer 1: JSON artifacts (必需)
# Layer 2: Knowledge graph (可选)
# Layer 3: Vector store (可选)
# Layer 4: Citation tracking (嵌入JSON)
```

### 4. **LLM 驱动规划**

```python
# 有 API key: 调用 Claude
# 无 API key: 使用启发式算法
# 支持 reference documents 注入
```

---

## 🚀 使用示例

### 基础使用

```python
from kosmos.ai_scientist.workflow import SCIResearchWorkflow
from kosmos.ai_scientist.supervisor import create_design_space

# 1. 创建 workflow
workflow = SCIResearchWorkflow(
    research_objective="优化SCI重建算法",
    design_space=create_design_space(),
    initial_configs=None,  # 跳过种子实验
    budget_max=50
)

# 2. 运行
results = await workflow.run(num_cycles=10, experiments_per_cycle=5)

# 3. 查看结果
print(f"最优PSNR: {results['best_metrics']['psnr']:.2f}dB")
print(f"Pareto前沿: {results['final_pareto_size']} 配置")
```

### 高级使用 (LLM 支持)

```python
from anthropic import Anthropic

# 初始化 LLM 客户端
client = Anthropic(api_key="your-api-key")

# 创建 workflow (启用 LLM)
workflow = SCIResearchWorkflow(
    research_objective="优化SCI重建算法",
    design_space=create_design_space(),
    anthropic_client=client,  # 传入客户端
    enable_llm_verification=True,  # 启用LLM验证
    budget_max=50
)

# 运行 (会使用 Claude 生成配置)
results = await workflow.run(num_cycles=10, experiments_per_cycle=5)
```

---

## 📈 性能示例

**典型运行结果**：

```
======================================================================
SCI Research Workflow Complete!
Experiments: 50
Cycles: 10
Pareto Frontier: 8 configurations
Best PSNR: 29.80dB
Time: 120.5s
======================================================================

Pareto前沿演化:
  Cycle 1: 2 configurations (5 experiments run)
  Cycle 2: 4 configurations (5 experiments run)
  Cycle 3: 5 configurations (5 experiments run)
  Cycle 4: 6 configurations (5 experiments run)
  Cycle 5: 7 configurations (5 experiments run)
  Cycle 6: 7 configurations (5 experiments run)
  Cycle 7: 8 configurations (5 experiments run)
  Cycle 8: 8 configurations (5 experiments run)
  Cycle 9: 8 configurations (5 experiments run)
  Cycle 10: 8 configurations (5 experiments run)
```

---

## 📚 总结

SCI Research Loop 实现了一个**完全自动化的科学实验优化流程**，核心特点：

✅ **自动化**: 从规划到执行到分析，全自动
✅ **智能化**: LLM 驱动的配置生成
✅ **优化**: Pareto 多目标优化
✅ **可追溯**: 完整的状态持久化
✅ **高效**: 配置去重避免重复实验
✅ **灵活**: 支持多种设计空间和优化目标

这就是完整的 SCI Research Loop 执行流程！🎉
