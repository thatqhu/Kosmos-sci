# SCI Research Loop 初始化方式更新

## 概述

`SCIResearchWorkflow` 现在支持更灵活的 LLM 客户端初始化方式。不再需要手动创建 Anthropic 或 OpenAI 客户端，可以直接传入 API token 和 URL。

## 更新内容

### 参数变更

**移除的参数:**
- `anthropic_client`: 预配置的 Anthropic 客户端

**新增的参数:**
- `api_token` (Optional[str]): API token/key
- `openapi_url` (Optional[str]): OpenAPI 兼容的端点 URL
- `llm_model` (str): LLM 模型名称，默认 "gemini-2.0-flash-exp"
- `llm_provider` (str): LLM 提供商，默认 "auto" (自动检测)

## 使用方式

### 方式 1: 显式指定 API token 和 URL (推荐用于生产环境)

```python
from kosmos.ai_scientist.workflow import SCIResearchWorkflow
import os

workflow = SCIResearchWorkflow(
    research_objective="优化 SCI 重建",
    design_space=design_space,
    # 直接传入配置
    api_token=os.getenv("GEMINI_API_KEY"),
    openapi_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    llm_model="gemini-2.0-flash-exp",
    llm_provider="openai",
    budget_max=50
)
```

### 方式 2: 完全自动 (推荐用于开发)

```python
# 不传任何 LLM 参数，系统会:
# 1. 自动从环境变量读取 API key (GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY)
# 2. 自动检测 provider 类型
# 3. 自动设置默认端点

workflow = SCIResearchWorkflow(
    research_objective="优化 SCI 重建",
    design_space=design_space,
    budget_max=50
)
```

### 方式 3: 使用本地 LLM (Ollama)

```python
workflow = SCIResearchWorkflow(
    research_objective="本地测试",
    design_space=design_space,
    api_token="ollama",  # Ollama 不需要真实 key
    openapi_url="http://localhost:11434/v1/",
    llm_model="llama2",
    llm_provider="openai",
    budget_max=20
)
```

### 方式 4: 使用 Anthropic Claude

```python
workflow = SCIResearchWorkflow(
    research_objective="使用 Claude 优化",
    design_space=design_space,
    api_token=os.getenv("ANTHROPIC_API_KEY"),
    llm_model="claude-sonnet-4-5",
    llm_provider="anthropic",
    budget_max=30
)
```

## 支持的 Provider

| Provider | 环境变量 | 默认模型 | 默认端点 |
|---------|---------|---------|---------|
| Gemini (推荐) | `GEMINI_API_KEY` | gemini-2.0-flash-exp | https://generativelanguage.googleapis.com/v1beta/openai/ |
| OpenAI | `OPENAI_API_KEY` | gpt-4 | https://api.openai.com/v1/ |
| Anthropic | `ANTHROPIC_API_KEY` | claude-sonnet-4-5 | (内置) |
| 本地 Ollama | - | llama2 | http://localhost:11434/v1/ |

## 环境变量设置

```bash
# Gemini (免费，推荐)
export GEMINI_API_KEY="your-gemini-api-key"

# Anthropic Claude
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# OpenAI
export OPENAI_API_KEY="your-openai-api-key"
```

## 迁移指南

### 旧代码 (v2.0)

```python
import anthropic

# 手动创建客户端
client = anthropic.Anthropic(api_key="your-key")

workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    anthropic_client=client,  # 传入预创建的客户端
    budget_max=50
)
```

### 新代码 (v2.1+)

```python
# 方式 A: 直接传入配置
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    api_token="your-key",
    llm_provider="anthropic",
    budget_max=50
)

# 方式 B: 从环境变量自动加载 (推荐)
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    budget_max=50
)
```

## 内部实现

新增的 `_initialize_llm_client()` 方法会:

1. 从参数或环境变量获取 API token
2. 根据 `llm_provider` 参数选择提供商（支持自动检测）
3. 创建相应的客户端（OpenAI 或 Anthropic）
4. 将客户端传递给 Planner 和 AnalysisAgent

## 错误处理

如果没有提供 API token 且环境变量中也没有：

```
⚠️ WARNING: No API token provided, LLM features will be disabled
```

工作流会继续运行，但使用 mock LLM 生成配置（用于测试）。

## 示例文件

- `examples/sci_workflow_simple.py` - 基础用法（自动加载）
- `examples/sci_workflow_with_openapi.py` - 多种初始化方式演示
- `examples/sci_workflow_with_references.py` - 带参考文档的规划

## 优势

✅ **更简洁**: 不需要手动创建客户端
✅ **更灵活**: 支持多个 LLM provider
✅ **更安全**: 自动从环境变量读取，避免硬编码
✅ **更智能**: 自动检测 provider 类型
✅ **向后兼容**: 旧的示例代码仍然可以工作

## 更新日期

2025-12-19
