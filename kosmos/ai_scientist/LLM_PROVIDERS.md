# LLM 提供商配置指南

SCI Research Loop 现在支持多个 LLM 提供商。本指南说明如何配置和使用不同的模型。

---

## 支持的提供商

### 1. **Google Gemini** (推荐 - 免费 API)

#### 特点
- ✅ 免费 API 额度
- ✅ 高性能
- ✅ OpenAI 兼容接口
- ✅ 支持长上下文

#### 获取 API Key
1. 访问 [Google AI Studio](https://aistudio.google.com/app/apikey)
2. 登录 Google 账号
3. 点击 "Create API Key"
4. 复制 API key

#### 配置
```bash
# 设置环境变量
export GEMINI_API_KEY=your-gemini-api-key

# 或在代码中设置
import os
os.environ["GEMINI_API_KEY"] = "your-key"
```

#### 使用示例
```python
from kosmos.ai_scientist.workflow import SCIResearchWorkflow

workflow = SCIResearchWorkflow(
    research_objective="优化 SCI 重建",
    design_space=design_space,
    # provider 会自动检测到 GEMINI_API_KEY
)

# 运行
results = await workflow.run(num_cycles=10)
```

#### 可用模型
- `gemini-2.0-flash-exp` (默认)
- `gemini-1.5-pro`
- `gemini-1.5-flash`

---

### 2. **Anthropic Claude**

#### 特点
- ✅ 高质量输出
- ✅ 强大的推理能力
- ⚠️ 需要付费

#### 获取 API Key
1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 创建账号并绑定付款方式
3. 生成 API key

#### 配置
```bash
export ANTHROPIC_API_KEY=your-anthropic-key
```

#### 使用示例
```python
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI 重建",
    design_space=design_space,
    # 明确指定使用 Anthropic
    # (或者不设置 GEMINI_API_KEY，会自动选择)
)

# 或者手动指定
from kosmos.ai_scientist.planner import Planner

planner = Planner(
    provider="anthropic",
    model="claude-sonnet-4-5",
    api_key="your-key"
)
```

#### 可用模型
- `claude-sonnet-4-5`
- `claude-3-5-sonnet-20241022`
- `claude-3-opus-20240229`

---

### 3. **其他 OpenAI 兼容的提供商**

#### 支持的服务
- OpenAI (ChatGPT)
- Azure OpenAI
- 本地部署的 LLM (Ollama, vLLM 等)

#### 配置
```python
from openai import OpenAI
from kosmos.ai_scientist.planner import Planner

# 方式 1: 使用环境变量
os.environ["OPENAI_API_KEY"] = "your-key"
planner = Planner(provider="openai", model="gpt-4")

# 方式 2: 自定义 base_url
planner = Planner(
    api_key="your-key",
    provider="openai",
    model="your-model",
    base_url="https://your-custom-endpoint/v1/"
)

# 方式 3: 传入已配置的客户端
client = OpenAI(
    api_key="your-key",
    base_url="http://localhost:11434/v1/"  # 例: Ollama
)
planner = Planner(openai_client=client, model="llama2")
```

---

## 自动检测逻辑

系统会按以下优先级自动检测使用哪个提供商：

1. **环境变量检测** (当 `provider="auto"`):
   ```
   GEMINI_API_KEY 存在 → 使用 Gemini/OpenAI
   OPENAI_API_KEY 存在 → 使用 OpenAI
   ANTHROPIC_API_KEY 存在 → 使用 Anthropic
   ```

2. **传入的客户端**:
   ```python
   Planner(openai_client=client)  # → 使用 OpenAI
   Planner(anthropic_client=client)  # → 使用 Anthropic
   ```

3. **显式指定**:
   ```python
   Planner(provider="anthropic")  # → 使用 Anthropic
   Planner(provider="openai")  # → 使用 OpenAI
   ```

---

## 完整配置示例

### Gemini (推荐)
```python
import asyncio
import os
from kosmos.ai_scientist.workflow import SCIResearchWorkflow

async def main():
    # 设置 API key
    os.environ["GEMINI_API_KEY"] = "your-gemini-api-key"

    # 创建工作流 (自动使用 Gemini)
    workflow = SCIResearchWorkflow(
        research_objective="优化 SCI",
        design_space=design_space,
        budget_max=50
    )

    # 验证配置
    print(f"Provider: {workflow.planner.provider}")  # 应该是 "openai"
    print(f"Model: {workflow.planner.model}")  # gemini-2.0-flash-exp

    # 运行
    results = await workflow.run(num_cycles=10)

asyncio.run(main())
```

### Anthropic Claude
```python
os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-key"

workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    budget_max=50
)

# 或者明确指定
workflow.planner.provider = "anthropic"
workflow.planner.model = "claude-sonnet-4-5"
```

### 本地 Ollama
```python
from openai import OpenAI

# 连接到本地 Ollama
client = OpenAI(
    api_key="ollama",  # Ollama 不需要真实 key
    base_url="http://localhost:11434/v1/"
)

# 创建工作流
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    budget_max=50
)

# 手动设置 planner 和 analysis_agent 使用本地模型
workflow.planner.client = client
workflow.planner.provider = "openai"
workflow.planner.model = "llama2"

workflow.analysis_agent.client = client
workflow.analysis_agent.provider = "openai"
workflow.analysis_agent.model = "llama2"
```

---

## 成本对比

| 提供商 | 模型 | 输入价格 | 输出价格 | 免费额度 |
|--------|------|---------|---------|---------|
| **Gemini** | 2.0 Flash | $0 | $0 | 1500 req/day |
| **Gemini** | 1.5 Pro | $1.25/1M | $5/1M | 50 req/day |
| Anthropic | Claude Sonnet 4.5 | $3/1M | $15/1M | 无 |
| OpenAI | GPT-4 Turbo | $10/1M | $30/1M | 无 |

**推荐**: 开发阶段使用 **Gemini 2.0 Flash**(免费)，生产环境根据需求选择。

---

## 故障排除

### 问题: "No module named 'openai'"
```bash
pip install openai
```

### 问题: "No module named 'anthropic'"
```bash
pip install anthropic
```

### 问题: "No API key provided"
```bash
# 检查环境变量
echo $GEMINI_API_KEY
echo $ANTHROPIC_API_KEY

# 如果为空，设置它
export GEMINI_API_KEY=your-key
```

### 问题: "Unknown provider"
- 确保 `provider` 参数是 "openai", "anthropic" 或 "auto"
- 确保安装了相应的 SDK 包

### 问题: Gemini API 调用失败
```python
# 检查 base_url 是否正确
planner = Planner(
    api_key="your-key",
    provider="openai",
    model="gemini-2.0-flash-exp",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
```

---

## 性能建议

### Planner (规划阶段)
- **推荐**: Gemini 2.0 Flash (快速 + 免费)
- **备选**: Claude Sonnet 4.5 (高质量)

### Analysis (分析阶段 - LLM 验证)
- **通常不需要启用** - 标准算法已足够
- 如果启用: Gemini 1.5 Flash (节省成本)

---

## 示例脚本

- **Gemini**: `examples/sci_workflow_gemini.py`
- **标准**: `examples/sci_workflow_example.py`
- **LLM 验证**: `examples/llm_verification_demo.py`

---

更新日期: 2025-12-18
版本: v2.1 (Multi-LLM Support)
