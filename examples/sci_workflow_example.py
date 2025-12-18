"""
示例: 如何使用改造后的SCI Research Workflow

这个例子展示了如何使用新的workflow架构运行SCI优化。
"""

import asyncio
import os
from kosmos.ai_scientist.workflow import SCIResearchWorkflow
from kosmos.ai_scientist.supervisor import create_design_space, create_initial_configs


async def main():
    """运行SCI优化示例。"""

    # 1. 定义设计空间
    design_space = create_design_space()

    # 2. 可选：定义种子配置
    initial_configs = create_initial_configs()

    # 3. 检查是否启用LLM功能
    api_key = os.getenv("ANTHROPIC_API_KEY")
    enable_llm = bool(api_key)

    if enable_llm:
        print("✓ ANTHROPIC_API_KEY detected, LLM features enabled")
    else:
        print("⚠ ANTHROPIC_API_KEY not set, using standard algorithms")

    # 4. 创建SCI研究工作流
    workflow = SCIResearchWorkflow(
        research_objective="优化Snapshot Compressive Imaging重建算法的PSNR和覆盖率",
        design_space=design_space,
        initial_configs=initial_configs,
        optimization_objectives=['psnr', 'coverage', 'latency'],
        artifacts_dir="./artifacts/sci_optimization",
        budget_max=50,
        enable_llm_verification=False  # 可以设为True启用LLM验证
    )

    # 5. 运行优化
    results = await workflow.run(
        num_cycles=10,
        experiments_per_cycle=5
    )

    # 6. 查看结果
    print("\n" + "="*70)
    print("最终优化结果")
    print("="*70)

    print(f"\n实验总数: {results['total_experiments']}")
    print(f"完成周期: {results['cycles_completed']}")
    print(f"Pareto前沿配置数: {results['final_pareto_size']}")

    if results['best_configuration']:
        print("\n最优配置:")
        config = results['best_configuration']
        metrics = results['best_metrics']

        print(f"  Reconstruction Family: {config['recon_family']}")
        print(f"  UQ Scheme: {config['uq_scheme']}")
        print(f"  Parameters: {config['recon_params']}")
        print(f"\n性能指标:")
        print(f"  PSNR: {metrics['psnr']:.2f} dB")
        print(f"  Coverage: {metrics['coverage']:.2%}")
        print(f"  Latency: {metrics['latency']:.1f} ms")

    print(f"\n总耗时: {results['total_time']:.1f}秒")

    # 7. Pareto前沿演化
    print("\nPareto前沿演化:")
    for entry in results['pareto_history']:
        print(
            f"  Cycle {entry['cycle']}: {entry['pareto_size']} configurations "
            f"({entry['experiments_run']} experiments run)"
        )

    # 8. 展示Kosmos集成接口 (新增)
    print("\n" + "="*70)
    print("Kosmos Integration Interface Demo")
    print("="*70)

    # 获取统计信息
    stats = workflow.get_statistics()
    print("\n统计信息:")
    print(f"  Workflow Type: {stats['workflow']['type']}")
    print(f"  LLM Planner Enabled: {stats['planner']['llm_enabled']}")
    print(f"  LLM Verification Enabled: {stats['analysis']['llm_verification_enabled']}")
    print(f"  Total Experiments: {stats['state_manager']['total_experiments']}")
    print(f"  Pareto Frontier Size: {stats['state_manager']['pareto_frontier_size']}")

    # 生成报告
    report = await workflow.generate_report()
    print("\n生成的研究报告 (前300字符):")
    print("-" * 70)
    print(report[:300] + "...")
    print("-" * 70)


if __name__ == "__main__":
    asyncio.run(main())
