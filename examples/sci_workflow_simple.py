"""
示例: SCI Research Workflow - 直接从LLM规划开始

这个例子展示了如何使用改造后的workflow，跳过种子实验，直接从LLM规划开始。

新特性 (v2.1+):
- 支持通过 api_token 和 openapi_url 直接初始化 LLM client
- 支持自动从环境变量读取 API key (GEMINI_API_KEY, ANTHROPIC_API_KEY 等)
- 支持多个 LLM provider: Gemini, Anthropic Claude, OpenAI, 本地 Ollama 等
"""

import asyncio
import os
from kosmos.ai_scientist.workflow import SCIResearchWorkflow
from kosmos.ai_scientist.supervisor import create_design_space


async def main():
    """运行SCI优化示例。"""

    # 1. 定义设计空间
    design_space = create_design_space()

    # 2. 创建SCI研究工作流
    #
    # 新版本支持两种初始化方式:
    #
    # 方式A (推荐): 直接传入 API token 和 URL
    # workflow = SCIResearchWorkflow(
    #     research_objective="优化SCI重建",
    #     design_space=design_space,
    #     api_token=os.getenv("GEMINI_API_KEY"),  # 从环境变量获取
    #     openapi_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    #     llm_model="gemini-2.0-flash-exp",
    #     llm_provider="openai",
    #     budget_max=50
    # )
    #
    # 方式B (最简单): 完全自动 - 从环境变量自动加载
    workflow = SCIResearchWorkflow(
        research_objective="优化Snapshot Compressive Imaging重建算法的PSNR和覆盖率",
        design_space=design_space,
        api_token=os.getenv("GEMINI_API_KEY"),  # 从环境变量获取
        openapi_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        initial_configs=None,  # None表示直接从LLM规划开始，不运行种子实验
        optimization_objectives=['psnr', 'coverage', 'latency'],
        artifacts_dir="./artifacts/sci_optimization",
        budget_max=50
        # 不传 api_token，会自动从环境变量读取:
        # GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY
    )

    # 3. 运行优化（第一个周期就会使用LLM生成配置）
    print("\n开始SCI优化工作流...")
    print("注意: 不会运行种子实验，直接从Cycle 1的LLM规划开始\n")

    results = await workflow.run(
        num_cycles=10,
        experiments_per_cycle=5
    )

    # 4. 查看结果
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

    # 5. Pareto前沿演化
    print("\nPareto前沿演化:")
    for entry in results['pareto_history']:
        print(
            f"  Cycle {entry['cycle']}: {entry['pareto_size']} configurations "
            f"({entry['experiments_run']} experiments run)"
        )


if __name__ == "__main__":
    asyncio.run(main())
