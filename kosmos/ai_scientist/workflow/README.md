# SCI Research Loop - 工作流说明

## 快速开始

### 最简单的方式（推荐）

```python
import asyncio
from kosmos.ai_scientist.workflow import SCIResearchWorkflow

# 1. 设置环境变量
# export GEMINI_API_KEY="your-api-key"

# 2. 定义设计空间
design_space = {
    "recon_families": ["CIAS-Core", "CIAS-Core-ELP"],
    "uq_schemes": ["Conformal", "None"],
}

# 3. 创建工作流（自动从环境变量读取 API key）
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI 重建性能",
    design_space=design_space,
    budget_max=50
)

# 4. 运行
results = await workflow.run(num_cycles=10, experiments_per_cycle=5)
```

## 初始化参数

### 核心参数

- `research_objective` (str): 研究目标描述
- `design_space` (dict): 配置空间定义
- `budget_max` (int): 最大实验次数，默认 50

### LLM 配置（新）

- `api_token` (str, 可选): API token，不传则从环境变量读取
- `openapi_url` (str, 可选): API 端点 URL
- `llm_model` (str): 模型名称，默认 "gemini-2.0-flash-exp"
- `llm_provider` (str): 提供商，默认 "auto" (自动检测)

### 其他参数

- `optimization_objectives` (list): 优化目标，默认 ['psnr', 'coverage']
- `enable_llm_verification` (bool): 启用 LLM 验证，默认 False
- `artifacts_dir` (str): 输出目录，默认 "artifacts/sci"
- `reference_docs` (list, 可选): 参考文档文本列表
- `reference_doc_paths` (list, 可选): 参考文档文件路径列表

## 多种初始化方式

### 1️⃣ 完全自动（最简单）

```python
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    budget_max=50
)
# 从环境变量自动读取: GEMINI_API_KEY, ANTHROPIC_API_KEY
```

### 2️⃣ 显式指定 Gemini

```python
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    api_token="your-gemini-key",
    openapi_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    llm_model="gemini-2.0-flash-exp",
    llm_provider="openai",
    budget_max=50
)
```

### 3️⃣ 使用 Anthropic Claude

```python
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    api_token="your-anthropic-key",
    llm_model="claude-sonnet-4-5",
    llm_provider="anthropic",
    budget_max=50
)
```

### 4️⃣ 本地 Ollama

```python
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    api_token="ollama",
    openapi_url="http://localhost:11434/v1/",
    llm_model="llama2",
    llm_provider="openai",
    budget_max=50
)
```

### 5️⃣ 带参考文档

```python
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    reference_doc_paths=["papers/sci_survey.pdf", "docs/guidelines.md"],
    budget_max=50
)
```

## 运行工作流

```python
# 基础运行
results = await workflow.run(
    num_cycles=10,           # 优化周期数
    experiments_per_cycle=5  # 每周期实验数
)

# 查看结果
print(f"总实验数: {results['total_experiments']}")
print(f"Pareto 前沿: {results['final_pareto_size']}")
print(f"最优 PSNR: {results['best_metrics']['psnr']:.2f} dB")
```

## 环境变量

支持的环境变量（按优先级）:

```bash
# Gemini (推荐，免费)
export GEMINI_API_KEY="your-key"

# OpenAI
export OPENAI_API_KEY="your-key"

# Anthropic
export ANTHROPIC_API_KEY="your-key"
```

## 文档

- **[初始化指南](INITIALIZATION_GUIDE.md)** - 详细的初始化方式和迁移指南
- **[更新总结](UPDATE_SUMMARY.md)** - v2.1 版本更新内容
- **[LLM 提供商](../LLM_PROVIDERS.md)** - 支持的 LLM 提供商和配置

## 示例代码

- `examples/sci_workflow_simple.py` - 基础示例
- `examples/sci_workflow_with_openapi.py` - 多种初始化方式演示
- `examples/sci_workflow_with_references.py` - 使用参考文档

## 常见问题

### Q: 没有 API key 可以运行吗？

A: 可以，但会使用 mock LLM（生成预定义的配置），适合测试流程。

### Q: 如何切换不同的 LLM？

A: 设置 `llm_provider` 参数为 "openai" 或 "anthropic"，或者设置相应的环境变量。

### Q: Gemini 是免费的吗？

A: 是的，Gemini 提供免费 API 额度，每天 1500 次请求。

### Q: 如何使用本地模型？

A: 设置 `openapi_url` 指向本地 Ollama 或 vLLM 服务端点。

## 版本历史

- **v2.1** (2025-12-19): 支持通过 api_token 和 openapi_url 初始化
- **v2.0**: 初始版本，需要手动创建客户端

## 相关组件

本工作流使用以下组件：

- **SCIStateManager**: 状态管理
- **SCIExecutorAgent**: 实验执行
- **Planner**: LLM 驱动的配置规划
- **AnalysisAgent**: Pareto 分析

## 支持

如有问题，请查看文档或提交 issue。
