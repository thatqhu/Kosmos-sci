"""
Gemini 配置示例

演示如何使用 Gemini (OpenAI兼容) 作为 LLM 模型
"""

import asyncio
import os
from kosmos.ai_scientist.workflow import SCIResearchWorkflow
from kosmos.ai_scientist.supervisor import create_design_space, create_initial_configs


async def main():
    """使用 Gemini 运行 SCI 优化示例。"""

    # 1. 设置 Gemini API Key
    # 获取免费 API key: https://aistudio.google.com/app/apikey
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("❌ 错误: GEMINI_API_KEY 环境变量未设置")
        print("请运行: export GEMINI_API_KEY=your-api-key")
        return

    print(f"✓ GEMINI_API_KEY 已设置 (长度: {len(api_key)})")

    # 2. 定义设计空间
    design_space = create_design_space()

    # 3. 定义种子配置
    initial_configs = create_initial_configs()

    # 4. 创建 SCI 研究工作流 (使用 Gemini)
    workflow = SCIResearchWorkflow(
        research_objective="优化 Snapshot Compressive Imaging 重建算法",
        design_space=design_space,
        initial_configs=initial_configs,
        optimization_objectives=['psnr', 'coverage', 'latency'],
        artifacts_dir="./artifacts/sci_gemini",
        budget_max=20,
        enable_llm_verification=False
    )

    print("\n" + "="*70)
    print("SCI 优化工作流 - Gemini 驱动")
    print("="*70)

    # 显示配置
    stats = workflow.get_statistics()
    print(f"\n配置信息:")
    print(f"  LLM Provider: {workflow.planner.provider}")
    print(f"  LLM Model: {workflow.planner.model}")
    print(f"  Planner LLM: {stats['planner']['llm_enabled']}")
    print(f"  Analysis LLM: {stats['analysis']['llm_verification_enabled']}")

    # 5. 运行优化 (较少周期用于演示)
    print("\n开始优化...")
    results = await workflow.run(
        num_cycles=3,
        experiments_per_cycle=2
    )

    # 6. 查看结果
    print("\n" + "="*70)
    print("优化结果")
    print("="*70)

    print(f"\n实验总数: {results['total_experiments']}")
    print(f"完成周期: {results['cycles_completed']}")
    print(f"Pareto 前沿配置数: {results['final_pareto_size']}")

    if results['best_configuration']:
        print("\n最优配置:")
        config = results['best_configuration']
        metrics = results['best_metrics']

        print(f"  Reconstruction Family: {config['recon_family']}")
        print(f"  UQ Scheme: {config['uq_scheme']}")
        print(f"\n性能指标:")
        print(f"  PSNR: {metrics['psnr']:.2f} dB")
        print(f"  Coverage: {metrics['coverage']:.2%}")
        print(f"  Latency: {metrics['latency']:.1f} ms")

    print(f"\n总耗时: {results['total_time']:.1f} 秒")

    # 7. 生成报告
    print("\n" + "="*70)
    print("生成研究报告")
    print("="*70)

    report = await workflow.generate_report()

    # 保存报告
    report_path = "./artifacts/sci_gemini/report.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ 报告已保存到: {report_path}")
    print(f"\n报告预览(前300字符):")
    print("-" * 70)
    print(report[:300] + "...")
    print("-" * 70)


if __name__ == "__main__":
    asyncio.run(main())
