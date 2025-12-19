"""
SCI Research Loop 使用示例 - 使用 OpenAPI 地址和 token 初始化

展示如何使用新的 API，直接传入 OpenAPI 地址和 API token 来初始化工作流。
"""

import asyncio
import os
from kosmos.ai_scientist.workflow.sci_research_loop import SCIResearchWorkflow


async def main():
    """使用 OpenAPI 地址和 token 初始化 SCI Research Loop"""

    # 定义设计空间
    design_space = {
        "recon_families": ["CIAS-Core", "CIAS-Core-ELP", "Baseline-CNN"],
        "uq_schemes": ["Conformal", "Ensemble", "None"],
        "compression_ratios": [8, 16, 32]
    }

    # 方式 1: 使用 Gemini API （推荐，免费）
    print("="*70)
    print("方式 1: 使用 Gemini API")
    print("="*70)

    workflow = SCIResearchWorkflow(
        research_objective="优化 SCI 重建性能，提高 PSNR 和覆盖率",
        design_space=design_space,
        # 直接传入 API token 和 URL
        api_token=os.getenv("GEMINI_API_KEY"),  # 从环境变量获取
        openapi_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        llm_model="gemini-2.0-flash-exp",
        llm_provider="openai",  # Gemini 使用 OpenAI 兼容接口
        # 其他参数
        budget_max=20,
        enable_llm_verification=False
    )

    # 运行工作流
    results = await workflow.run(num_cycles=3, experiments_per_cycle=3)

    print(f"\n完成实验: {results['total_experiments']}个")
    print(f"Pareto 前沿: {results['final_pareto_size']}个配置")


    # 方式 2: 使用自定义 OpenAPI 端点 (例如本地 Ollama)
    print("\n" + "="*70)
    print("方式 2: 使用本地 Ollama")
    print("="*70)

    workflow_local = SCIResearchWorkflow(
        research_objective="本地测试 SCI 优化",
        design_space=design_space,
        # 本地 Ollama 配置
        api_token="ollama",  # Ollama 不需要真实 key
        openapi_url="http://localhost:11434/v1/",
        llm_model="llama2",
        llm_provider="openai",
        budget_max=10
    )

    print("已初始化本地 Ollama 工作流")


    # 方式 3: 使用 Anthropic Claude
    print("\n" + "="*70)
    print("方式 3: 使用 Anthropic Claude")
    print("="*70)

    if os.getenv("ANTHROPIC_API_KEY"):
        workflow_claude = SCIResearchWorkflow(
            research_objective="使用 Claude 优化 SCI",
            design_space=design_space,
            api_token=os.getenv("ANTHROPIC_API_KEY"),
            llm_model="claude-sonnet-4-5",
            llm_provider="anthropic",
            budget_max=15
        )
        print("已初始化 Anthropic Claude 工作流")
    else:
        print("⚠️ 未找到 ANTHROPIC_API_KEY 环境变量")


    # 方式 4: 自动检测（最简单）
    print("\n" + "="*70)
    print("方式 4: 自动检测 (推荐)")
    print("="*70)

    # 只需提供 API token，系统会自动检测使用哪个 provider
    workflow_auto = SCIResearchWorkflow(
        research_objective="自动检测 LLM provider",
        design_space=design_space,
        api_token=os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
        llm_provider="auto",  # 自动检测
        budget_max=15
    )

    print(f"已自动检测 provider: {workflow_auto.planner.provider}")


    # 方式 5: 从环境变量自动加载 (最简洁)
    print("\n" + "="*70)
    print("方式 5: 完全自动 (最简洁)")
    print("="*70)

    # 不传任何 LLM 参数，从环境变量自动加载
    workflow_env = SCIResearchWorkflow(
        research_objective="从环境变量自动初始化",
        design_space=design_space,
        budget_max=10
        # 不传 api_token 和 openapi_url，会自动从环境变量读取
        # 支持: GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY
    )

    if workflow_env.llm_client:
        print("✓ LLM 客户端已从环境变量自动初始化")
    else:
        print("⚠️ 未找到 API key 环境变量")


if __name__ == "__main__":
    # 确保设置了至少一个 API key
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("⚠️ 警告: 未设置 API key 环境变量")
        print("请设置以下之一:")
        print("  export GEMINI_API_KEY='your-key'")
        print("  export ANTHROPIC_API_KEY='your-key'")
        print("\n继续运行将使用 mock LLM...")

    asyncio.run(main())
