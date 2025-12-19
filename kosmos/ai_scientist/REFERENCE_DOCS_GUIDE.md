# Reference Documents for SCI Planning

## 参考文档功能说明

从 v2.3 开始，SCI AI Scientist 支持在规划阶段使用参考文档（论文、技术文档、指南等）来指导 LLM 生成更好的实验配置。

---

## 🎯 功能概述

### **为什么需要参考文档？**

LLM 进行实验规划时，如果有领域知识作为参考，可以：

1. **更准确的假设** - 基于已发表的研究结果
2. **避免已知陷阱** - 参考论文中的经验教训
3. **探索有前景的方向** - 基于相关工作的启发
4. **更合理的参数选择** - 参考论文中的最佳实践

### **支持的文档格式**

- ✅ **文本文件** (`.txt`)
- ✅ **Markdown** (`.md`, `.markdown`)
- ✅ **PDF** (`.pdf` - 需要 PyPDF2)
- ✅ **直接文本** (字符串)

---

## 📝 使用方法

### **方法 1: 直接传入文本**

```python
from kosmos.ai_scientist.workflow import SCIResearchWorkflow

# 定义参考文档内容
reference_text = """
SCI Reconstruction Best Practices (CVPR 2024)

Key findings:
- CIAS-Core-ELP architecture shows superior performance on mid-resolution datasets
- Conformal prediction provides better calibration than ensemble methods
- Learning rate of 0.001 with cosine annealing works best
- Layer count between 8-12 provides optimal trade-off
"""

# 创建工作流
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI 重建",
    design_space=design_space,
    budget_max=50,
    reference_docs=[reference_text]  # ← 传入文本
)

# LLM 会在规划时参考这些内容！
results = await workflow.run(num_cycles=10)
```

### **方法 2: 从文件加载**

```python
# 创建工作流，指定文档路径
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI 重建",
    design_space=design_space,
    budget_max=50,
    reference_doc_paths=[
        "/path/to/papers/sci_paper_2024.pdf",
        "/path/to/docs/cias_guide.md",
        "/path/to/notes/experiment_notes.txt"
    ]
)

# Planner 会自动加载这些文档
results = await workflow.run(num_cycles=10)
```

### **方法 3: 混合使用**

```python
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI 重建",
    design_space=design_space,
    budget_max=50,
    reference_docs=[quick_note],  # 直接文本
    reference_doc_paths=[          # 文件路径
        "papers/sci_review.pdf",
        "docs/architecture_guide.md"
    ]
)
```

---

## 📚 推荐的参考文档类型

### 1. **相关论文**

```
paper_summary = """
Paper: "Efficient Snapshot Compressive Imaging via Deep Learning"
Authors: Smith et al., CVPR 2024

Key contributions:
- Proposed CIAS-Core-ELP architecture
- Achieved SOTA results: PSNR=32.5dB on benchmark
- Recommended hyperparameters:
  * Learning rate: 1e-3
  * Layers: 10
  * Hidden dim: 128

Lessons learned:
- Deeper networks (>15 layers) lead to overfitting
- Ensemble methods increase latency significantly
"""

workflow = SCIResearchWorkflow(
    ...,
    reference_docs=[paper_summary]
)
```

### 2. **实验总结**

```
experiment_log = """
Previous Experiment Log - Week 3

Successful combinations:
✓ CIAS-Core + Conformal: PSNR=30.2
✓ CIAS-Core-ELP + Ensemble: PSNR=31.5

Failed approaches:
✗ Baseline-CNN + Conformal: Poor coverage (0.65)
✗ CIAS-Core with >12 layers: Overfitting

Next directions to explore:
- CIAS-Core-ELP with Conformal (not tested yet)
- Lower learning rates for better convergence
"""
```

### 3. **技术指南**

```
architecture_guide = """
CIAS Architecture Selection Guide

CIAS-Core:
- Best for: Low-resolution datasets (< 256x256)
- Pros: Fast training, stable
- Cons: Lower peak performance

CIAS-Core-ELP:
- Best for: Mid-resolution (256x512)
- Pros: Higher accuracy
- Cons: Slower inference

Baseline-CNN:
- Best for: Baseline comparisons
- Pros: Simple, interpretable
- Cons: Not competitive
"""
```

### 4. **UQ 方法指南**

```
uq_guide = """
Uncertainty Quantification Methods

Conformal Prediction:
- Calibration: Excellent (0.90+ coverage typical)
- Latency: Fast (<10ms overhead)
- Recommended when: Calibration is critical

Ensemble:
- Calibration: Good (0.85+ coverage)
- Latency: Slow (~5x inference time)
- Recommended when: Accuracy is priority

None:
- Use for: Baseline comparisons only
"""
```

---

## 🔍 LLM 如何使用文档

### **提示结构**

```
You are an AI experiment designer for snapshot compressive imaging (SCI).

Current state:
- Under-explored regions: uq_scheme:Ensemble
- Pareto frontier: 3 configurations
- Remaining budget: 10 experiments

## Reference Materials

### Reference Document 1: sci_paper_2024.pdf
```
Paper: "Efficient SCI via Deep Learning"
...
[文档内容]
...
```

### Reference Document 2: experiment_notes.md
```
Week 3 Experiment Log
...
[文档内容]
...
```

## Task

Based on the above information and reference materials, propose 3 new configurations.

Priority: Focus on under-explored regions while leveraging insights from the reference documents.
```

### **LLM 决策过程**

1. **理解当前状态** - 查看已探索的配置和 Pareto 前沿
2. **参考文档** - 找到相关建议和最佳实践
3. **综合决策** - 结合当前状态和文档知识
4. **生成配置** - 提出新的实验配置

**示例输出**:

```json
[
  {
    "recon_family": "CIAS-Core-ELP",
    "uq_scheme": "Ensemble",
    "recon_params": {"num_layers": 10, "hidden_dim": 128},
    "reasoning": "Based on CVPR 2024 paper: CIAS-Core-ELP + Ensemble achieves best accuracy. Using recommended 10 layers."
  },
  {
    "recon_family": "CIAS-Core",
    "uq_scheme": "Ensemble",
    "recon_params": {"num_layers": 8, "hidden_dim": 64},
    "reasoning": "Exploring Ensemble with lighter CIAS-Core as mentioned in experiment log."
  }
]
```

---

## 💡 最佳实践

### **1. 提供关键信息，避免冗余**

```python
# ✓ 好的做法
reference = """
SCI Paper Summary (CVPR 2024)
- CIAS-Core-ELP: PSNR=32.5 (best)
- Recommended layers: 8-12
- Learning rate: 1e-3
"""

# ✗ 避免
reference = """
[整篇 30 页论文的完整文本，包括引言、相关工作、实验细节...]
"""
# 太长会被截断，且 LLM 难以提取关键信息
```

### **2. 结构化文档**

```markdown
# ✓ 清晰的结构
## Architecture Comparison
- CIAS-Core: PSNR=30.2
- CIAS-Core-ELP: PSNR=32.5

## Recommended Parameters
- Layers: 10
- LR: 0.001

# ✗ 混乱的文本
CIAS-Core got 30.2 PSNR but CIAS-Core-ELP is better at 32.5. Try using 10 layers maybe? Learning rate could be 0.001...
```

### **3. 包含失败案例**

```python
reference = """
What NOT to do:
- ✗ Baseline-CNN + Ensemble: Poor results (PSNR < 25)
- ✗ >15 layers: Overfitting issues
- ✗ LR > 0.01: Training instability
"""
```

### **4. 定期更新文档**

```python
# 每几个周期更新一次
cycle_5_notes = """
Update (Cycle 5):
- Found: CIAS-Core-ELP + Conformal achieves 33.2 PSNR
- Note: This combination outperforms Ensemble variant
"""

# 在后续周期传入更新的文档
workflow.planner.reference_docs.append({
    'source': 'cycle_5_update',
    'content': cycle_5_notes
})
```

---

## 🎨 完整示例

```python
import asyncio
from kosmos.ai_scientist.workflow import SCIResearchWorkflow
from kosmos.ai_scientist.supervisor import create_design_space

async def main():
    # 1. 准备参考文档
    paper_summary = """
    SCI Optimization Guide (ICCV 2024)

    Architecture Performance:
    - CIAS-Core: PSNR=30.2, Latency=15ms
    - CIAS-Core-ELP: PSNR=32.5, Latency=25ms

    UQ Methods:
    - Conformal: Coverage=0.92, Fast
    - Ensemble: Coverage=0.88, 5x slower

    Best Practices:
    - Use 8-12 layers for optimal performance
    - LR=0.001 with cosine annealing
    - Avoid >15 layers (overfitting risk)
    """

    experiment_notes = """
    Week 2 Findings:

    Successful:
    ✓ CIAS-Core + Conformal: Good baseline
    ✓ CIAS-Core-ELP + None: Fast inference

    To explore:
    - CIAS-Core-ELP + Conformal (promising)
    - Lower LR for CIAS-Core-ELP
    """

    # 2. 创建工作流
    workflow = SCIResearchWorkflow(
        research_objective="找到最优 SCI 配置",
        design_space=create_design_space(),
        budget_max=30,
        reference_docs=[paper_summary],
        reference_doc_paths=["notes/experiment_notes.md"]
    )

    # 3. 运行优化
    print("="*70)
    print("开始 SCI 优化 (带参考文档)")
    print("="*70)

    results = await workflow.run(num_cycles=5, experiments_per_cycle=3)

    # 4. 查看结果
    print(f"\n最优配置: {results['best_configuration']}")
    print(f"PSNR: {results['best_metrics']['psnr']:.2f} dB")

    return results

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 效果对比

### **无参考文档**

```
Cycle 1: 随机探索
  → 提案: CIAS-Core + Conformal, Baseline-CNN + None, ...

Cycle 2: 基于结果探索
  → 可能重复无效组合

效率: 中等
```

### **有参考文档**

```
Cycle 1: 基于论文推荐
  → 提案: CIAS-Core-ELP + Conformal (论文推荐)

Cycle 2: 结合文档和结果
  → 避免已知失败组合
  → 探索论文提到的有前景方向

效率: 高
```

---

## ⚙️ 高级配置

### **文档长度限制**

```python
# 默认：每个文档截断到 2000 字符
# 如需调整，可以修改 Planner.build_planner_prompt 中的逻辑

# 或者预先总结文档
def summarize_paper(filepath):
    full_text = read_paper(filepath)
    # 使用 LLM 生成摘要
    summary = llm.summarize(full_text, max_length=1000)
    return summary

workflow = SCIResearchWorkflow(
    ...,
    reference_docs=[summarize_paper("long_paper.pdf")]
)
```

### **动态添加文档**

```python
# 初始化
workflow = SCIResearchWorkflow(...)

# 运行几个周期后
results_cycle_3 = await workflow.run(num_cycles=3)

# 根据结果添加新文档
new_insight = f"""
Mid-experiment Update:
- Current best: PSNR={results_cycle_3['best_metrics']['psnr']}
- Observation: Conformal shows better calibration
- Next: Try parameter variations of best config
"""

workflow.planner.reference_docs.append({
    'source': 'mid_experiment',
    'content': new_insight
})

# 继续优化
results_final = await workflow.run(num_cycles=7, start_cycle=4)
```

---

## 🐛 故障排除

### **PDF 读取失败**

```bash
# 如果遇到错误: PyPDF2 not installed
pip install PyPDF2

# 或使用预先提取的文本
pdf_text = extract_text_from_pdf("paper.pdf")  # 使用其他工具
workflow = SCIResearchWorkflow(..., reference_docs=[pdf_text])
```

### **文档太长被截断**

```python
# 查看日志
# [WARNING] Document truncated: paper.pdf (10000 chars → 2000 chars)

# 解决方案: 使用摘要
summary = create_summary(long_document)
workflow = SCIResearchWorkflow(..., reference_docs=[summary])
```

### **LLM 没有使用文档**

```python
# 检查文档是否加载
print(f"Loaded docs: {len(workflow.planner.reference_docs)}")

# 检查提示
# Planner 会在 build_planner_prompt 中包含文档
# 可以启用 DEBUG 日志查看完整提示
import logging
logging.getLogger('kosmos.ai_scientist.planner').setLevel(logging.DEBUG)
```

---

## 📚 总结

**参考文档功能让 LLM 规划更智能**:

- ✅ 基于已知知识而非盲目探索
- ✅ 避免重复已知的失败尝试
- ✅ 更快找到最优配置
- ✅ 支持多种文档格式
- ✅ 易于使用和扩展

**推荐工作流程**:

1. 收集相关论文/文档
2. 提取关键信息（摘要、最佳实践）
3. 传入 SCIResearchWorkflow
4. 运行优化
5. 根据结果更新文档
6. 继续优化

---

**版本**: v2.3
**日期**: 2025-12-19
**状态**: ✅ 已实现
