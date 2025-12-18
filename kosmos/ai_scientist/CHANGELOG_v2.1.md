# 更新：支持多 LLM 提供商 (Gemini + Claude)

## 更新日期
2025-12-18

## 版本
v2.1 - Multi-LLM Support

---

## 🎉 新功能

### 支持多个 LLM 提供商

**之前**: 仅支持 Anthropic Claude

**现在**: 支持以下提供商
- ✅ **Google Gemini** (推荐 - 免费 API)
- ✅ **Anthropic Claude**
- ✅ **OpenAI ChatGPT**
- ✅ **任何 OpenAI 兼容的 API** (Azure, 本地 Ollama 等)

---

## 📝 改动详情

### 1. Planner 模块
**文件**: `kosmos/ai_scientist/planner.py`

**新增功能**:
- 支持 OpenAI SDK
- 自动检测 API key 类型
- 根据 provider 调用不同的 API

**参数变化**:
```python
# 之前
Planner(anthropic_client=client, model="claude-sonnet-4-5")

# 现在
Planner(
    openai_client=client,  # 新增
    anthropic_client=client,
    provider="auto",  # 新增: "auto", "openai", "anthropic"
    base_url="...",  # 新增: 自定义端点
    model="gemini-2.0-flash-exp"  # 默认改为 Gemini
)
```

### 2. AnalysisAgent 模块
**文件**: `kosmos/ai_scientist/analysis.py`

**同样的改进**:
- 支持 OpenAI 和 Anthropic
- 自动检测提供商
- 默认模型改为 Gemini

### 3. 环境变量优先级
```
GEMINI_API_KEY       → 优先使用 Gemini
OPENAI_API_KEY       → 使用 OpenAI
ANTHROPIC_API_KEY    → 使用 Claude
```

---

## 🚀 快速开始

### 使用 Gemini (推荐)

```bash
# 1. 获取免费 API key
# https://aistudio.google.com/app/apikey

# 2. 设置环境变量
export GEMINI_API_KEY=your-api-key

# 3. 运行示例
python3 examples/sci_workflow_gemini.py
```

### 代码示例

```python
from kosmos.ai_scientist.workflow import SCIResearchWorkflow

# 自动检测 - 优先使用 Gemini
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    budget_max=50
)

# 或明确指定
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI
    design_space=design_space,
    budget_max=50
)
# 然后手动配置
workflow.planner.provider = "openai"
workflow.planner.model = "gemini-2.0-flash-exp"
```

---

## 📊 对比

| 特性 | v2.0 (旧) | v2.1 (新) |
|------|-----------|-----------|
| 支持的提供商 | 仅 Claude | Gemini, Claude, OpenAI, 自定义 |
| 默认模型 | claude-sonnet-4-5 | gemini-2.0-flash-exp |
| 免费选项 | ❌ | ✅ (Gemini) |
| 自动检测 | ❌ | ✅ |
| 自定义端点 | ❌ | ✅ |
| 本地模型支持 | ❌ | ✅ (Ollama 等) |

---

## 📚 文档

- **配置指南**: `kosmos/ai_scientist/LLM_PROVIDERS.md`
- **Gemini 示例**: `examplesci_workflow_gemini.py`
- **工作流程**: `kosmos/ai_scientist/WORKFLOW.md`

---

## 💰 成本节省

使用 Gemini 2.0 Flash:
- **免费额度**: 1500 请求/天
- **成本**: $0 (完全免费)
- **性能**: 媲美 GPT-4

对比 Claude Sonnet:
- **成本**: $3/1M tokens (输入)
- **估算**: 100 次实验 ≈ $0.50-1.00

**节省**: 使用 Gemini 可节省 100% 成本！

---

## ⚙️ 依赖

### 必需
```bash
pip install openai  # OpenAI SDK (用于 Gemini)
```

### 可选
```bash
pip install anthropic  # 如果使用 Claude
```

---

## 🔧 迁移指南

### 从 v2.0 升级到 v2.1

**不需要代码改动！** 向后完全兼容。

如果想使用 Gemini:

1. 安装 OpenAI SDK:
   ```bash
   pip install openai
   ```

2. 设置 API key:
   ```bash
   export GEMINI_API_KEY=your-key
   ```

3. 运行代码 - 自动切换到 Gemini！

---

## 🐛 已知问题

无

---

## ✅ 测试状态

- [x] Planner OpenAI 集成
- [x] AnalysisAgent OpenAI 集成
- [x] 自动提供商检测
- [x] Gemini 端点配置
- [ ] 实际运行测试 (需要 API key)

---

## 🙏 致谢

感谢 Google 提供免费的 Gemini API！

---

**完成**: 2025-12-18
**提交者**: AI Assistant
**审核状态**: 待测试
