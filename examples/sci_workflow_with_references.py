"""
SCI Workflow with Reference Documents Example

演示如何使用参考文档来指导 LLM 进行更智能的实验规划。
"""

import asyncio
import os
from kosmos.ai_scientist.workflow import SCIResearchWorkflow
from kosmos.ai_scientist.supervisor import create_design_space, create_initial_configs


# 示例参考文档
PAPER_SUMMARY = """
SCI Reconstruction Optimization - Best Practices (CVPR 2024)

## Architecture Comparison

Performance on Standard Benchmark:
- **CIAS-Core**: PSNR=30.2dB, Latency=15ms
  * Best for: Low-resolution, fast inference
  * Recommended layers: 6-8

- **CIAS-Core-ELP**: PSNR=32.5dB, Latency=25ms
  * Best for: High-accuracy requirements
  * Recommended layers: 10-12
  * Sweet spot: 10 layers with hidden_dim=128

- **Baseline-CNN**: PSNR=28.1dB, Latency=12ms
  * Use as baseline only
  * Not competitive for production

## Uncertainty Quantification

Methods tested:
- **Conformal Prediction**: Coverage=0.92, Overhead=<5ms
  * Excellent calibration
  * Minimal latency impact
  * Recommended for most cases

- **Ensemble**: Coverage=0.88, Overhead=~5x
  * Good accuracy but expensive
  * Use when latency is not critical

- **None**: No UQ
  * Baseline only

## Training Recommendations

Optimal hyperparameters found:
- Learning rate: 1e-3 (0.001)
- Scheduler: Cosine annealing
- Epochs: 50-100 (depending on dataset size)
- Batch size: 16-32

## Common Pitfalls

Avoid these combinations:
- ✗ CIAS-Core-ELP with >15 layers → Overfitting
- ✗ Baseline-CNN with Ensemble → Poor results, high latency
- ✗ Learning rate >0.01 → Training instability
- ✗ Too few layers (<5) → Underfitting
"""

EXPERIMENT_NOTES = """
Week 2 Experiment Log

## Successful Configurations

✓ Config A: CIAS-Core + Conformal
  - PSNR: 30.5 dB
  - Coverage: 0.91
  - Latency: 18 ms
  - Notes: Good baseline, stable training

✓ Config B: CIAS-Core-ELP + None (no UQ)
  - PSNR: 32.1 dB
  - Coverage: N/A
  - Latency: 22 ms
  - Notes: Fast, but no uncertainty estimates

## Failed Attempts

✗ Config X: Baseline-CNN + Ensemble
  - PSNR: 27.3 dB (too low)
  - Latency: 65 ms (too slow)
  - Reason: Baseline architecture is weak

✗ Config Y: CIAS-Core with 16 layers
  - PSNR: 28.9 dB (worse than 10 layers!)
  - Reason: Overfitting, as predicted in literature

## Unexplored Combinations

Priority to test next:
1. CIAS-Core-ELP + Conformal
   - Expected: High PSNR + good calibration
   - Risk: Moderate latency increase

2. CIAS-Core + Ensemble
   - Expected: Better than Conformal on accuracy
   - Risk: High latency

3. Parameter variations of Config B
   - Try different layer counts (9, 11, 12)
   - Try different learning rates
"""


async def main():
    """使用参考文档运行 SCI 优化"""

    # 检查 API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 GEMINI_API_KEY 或 OPENAI_API_KEY")
        print("请运行: export GEMINI_API_KEY=your-api-key")
        return

    print("="*80)
    print("SCI优化工作流 - 带参考文档指导")
    print("="*80)

    # 创建设计空间
    design_space = create_design_space()

    # 创建种子配置
    initial_configs = create_initial_configs()

    # 创建工作流 - 传入参考文档
    workflow = SCIResearchWorkflow(
        research_objective="优化 Snapshot Compressive Imaging 重建算法",
        design_space=design_space,
        initial_configs=initial_configs,
        optimization_objectives=['psnr', 'coverage', 'latency'],
        artifacts_dir="./artifacts/sci_with_docs",
        budget_max=25,
        enable_llm_verification=False,

        # ← 关键: 传入参考文档
        reference_docs=[
            PAPER_SUMMARY,      # 论文总结
            EXPERIMENT_NOTES    # 实验笔记
        ]
    )

    print("\n" + "="*80)
    print("配置信息")
    print("="*80)

    stats = workflow.get_statistics()
    print(f"\nLLM 配置:")
    print(f"  Provider: {workflow.planner.provider}")
    print(f"  Model: {workflow.planner.model}")
    print(f"  Planner LLM: {stats['planner']['llm_enabled']}")

    # 显示加载的参考文档
    if workflow.planner.reference_docs:
        print(f"\n参考文档:")
        for i, doc in enumerate(workflow.planner.reference_docs, 1):
            source = doc['source']
            content_length = len(doc['content'])
            preview = doc['content'][:100].replace('\n', ' ')
            print(f"  {i}. {source} ({content_length} chars)")
            print(f"     预览: {preview}...")

    # 运行优化
    print("\n" + "="*80)
    print("开始优化")
    print("="*80)

    print("\n💡 LLM 会根据参考文档:")
    print("  - 优先尝试论文推荐的配置 (CIAS-Core-ELP, 10layers)")
    print("  - 避免已知失败组合 (Baseline-CNN + Ensemble)")
    print("  - 探索实验笔记中的未测试组合")
    print()

    results = await workflow.run(
        num_cycles=4,
        experiments_per_cycle=3
    )

    # 查看结果
    print("\n" + "="*80)
    print("优化结果")
    print("="*80)

    print(f"\n实验统计:")
    print(f"  总实验数: {results['total_experiments']}")
    print(f"  完成周期: {results['cycles_completed']}")
    print(f"  Pareto 前沿: {results['final_pareto_size']} 个配置")

    if results['best_configuration']:
        print(f"\n🏆 最优配置:")
        config = results['best_configuration']
        metrics = results['best_metrics']

        print(f"  架构: {config['recon_family']}")
        print(f"  UQ 方案: {config['uq_scheme']}")
        print(f"  参数: {config['recon_params']}")

        print(f"\n📊 性能:")
        print(f"  PSNR: {metrics['psnr']:.2f} dB")
        print(f"  Coverage: {metrics['coverage']:.2%}")
        print(f"  Latency: {metrics['latency']:.1f} ms")

    print(f"\n⏱️  总耗时: {results['total_time']:.1f} 秒")

    # 生成报告
    print("\n" + "="*80)
    print("生成研究报告")
    print("="*80)

    report = await workflow.generate_report()

    report_path = "./artifacts/sci_with_docs/report_with_references.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ 报告已保存: {report_path}")

    # 显示报告片段
    print(f"\n报告预览:")
    print("-" * 80)
    lines = report.split('\n')
    print('\n'.join(lines[:20]))
    if len(lines) > 20:
        print(f"... ({len(lines) - 20} more lines)")
    print("-" * 80)

    return results


async def demo_with_doc_files():
    """演示: 从文件加载参考文档"""

    print("\n" + "="*80)
    print("示例: 从文件加载参考文档")
    print("="*80)

    # 创建示例文档文件
    docs_dir = "./artifacts/reference_docs"
    os.makedirs(docs_dir, exist_ok=True)

    paper_file = f"{docs_dir}/sci_paper_summary.md"
    with open(paper_file, 'w', encoding='utf-8') as f:
        f.write(PAPER_SUMMARY)
    print(f"✓ 创建文档: {paper_file}")

    notes_file = f"{docs_dir}/experiment_notes.txt"
    with open(notes_file, 'w', encoding='utf-8') as f:
        f.write(EXPERIMENT_NOTES)
    print(f"✓ 创建文档: {notes_file}")

    # 使用文件路径创建工作流
    workflow = SCIResearchWorkflow(
        research_objective="SCI 优化",
        design_space=create_design_space(),
        budget_max=10,

        # 从文件加载
        reference_doc_paths=[
            paper_file,
            notes_file
        ]
    )

    print(f"\n✓ 已加载 {len(workflow.planner.reference_docs)} 个文档")

    for i, doc in enumerate(workflow.planner.reference_docs, 1):
        print(f"  {i}. {doc['source']}")


if __name__ == "__main__":
    # 运行主示例
    asyncio.run(main())

    # （可选）演示文件加载
    # asyncio.run(demo_with_doc_files())
