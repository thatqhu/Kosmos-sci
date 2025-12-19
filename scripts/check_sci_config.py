#!/usr/bin/env python3
"""
配置助手：帮助用户快速配置 SCI Research Loop

提供交互式配置向导和配置验证功能
"""

import os
import sys


def check_environment():
    """检查环境变量配置"""
    print("="*70)
    print("🔍 检查 LLM 配置")
    print("="*70)

    env_vars = {
        "GEMINI_API_KEY": "Gemini API (推荐，免费)",
        "ANTHROPIC_API_KEY": "Anthropic Claude API",
        "OPENAI_API_KEY": "OpenAI API"
    }

    found_keys = []

    for var, description in env_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else value
            print(f"✅ {var}")
            print(f"   描述: {description}")
            print(f"   值: {masked}")
            found_keys.append(var)
        else:
            print(f"❌ {var}")
            print(f"   描述: {description}")
            print(f"   状态: 未设置")
        print()

    if found_keys:
        print(f"✅ 找到 {len(found_keys)} 个配置的 API key")
        print(f"   推荐使用: {found_keys[0]}")
    else:
        print("⚠️  未找到任何 API key")
        print("\n建议设置环境变量:")
        print("  export GEMINI_API_KEY='your-key'  # 推荐，免费")

    return len(found_keys) > 0


def show_quick_start():
    """显示快速开始代码"""
    print("\n" + "="*70)
    print("🚀 快速开始代码")
    print("="*70)

    code = '''
import asyncio
from kosmos.ai_scientist.workflow import SCIResearchWorkflow

async def main():
    # 定义设计空间
    design_space = {
        "recon_families": ["CIAS-Core", "CIAS-Core-ELP"],
        "uq_schemes": ["Conformal", "None"],
    }

    # 创建工作流（自动从环境变量读取 API key）
    workflow = SCIResearchWorkflow(
        research_objective="优化 SCI 重建性能",
        design_space=design_space,
        budget_max=20
    )

    # 运行
    results = await workflow.run(num_cycles=3, experiments_per_cycle=3)

    print(f"完成 {results['total_experiments']} 个实验")
    print(f"Pareto 前沿: {results['final_pareto_size']} 个配置")

if __name__ == "__main__":
    asyncio.run(main())
'''

    print(code)
    print("\n保存上述代码到 my_experiment.py 并运行:")
    print("  python3 my_experiment.py")


def suggest_provider():
    """根据环境变量建议使用哪个 provider"""
    print("\n" + "="*70)
    print("💡 Provider 建议")
    print("="*70)

    if os.getenv("GEMINI_API_KEY"):
        print("✅ 推荐使用: Gemini")
        print("   原因: 免费、快速、性能好")
        print("   配置: 已检测到 GEMINI_API_KEY")
        print("\n   代码示例:")
        print("   workflow = SCIResearchWorkflow(")
        print("       research_objective='优化 SCI',")
        print("       design_space=design_space,")
        print("       # 会自动使用 Gemini")
        print("   )")

    elif os.getenv("ANTHROPIC_API_KEY"):
        print("✅ 推荐使用: Anthropic Claude")
        print("   原因: 高质量输出")
        print("   配置: 已检测到 ANTHROPIC_API_KEY")
        print("\n   代码示例:")
        print("   workflow = SCIResearchWorkflow(")
        print("       research_objective='优化 SCI',")
        print("       design_space=design_space,")
        print("       llm_provider='anthropic'")
        print("   )")

    elif os.getenv("OPENAI_API_KEY"):
        print("✅ 推荐使用: OpenAI")
        print("   原因: 强大的能力")
        print("   配置: 已检测到 OPENAI_API_KEY")
        print("\n   代码示例:")
        print("   workflow = SCIResearchWorkflow(")
        print("       research_objective='优化 SCI',")
        print("       design_space=design_space,")
        print("       llm_provider='openai'")
        print("   )")

    else:
        print("⚠️  未找到 API key")
        print("\n推荐设置 Gemini API key (免费):")
        print("  1. 访问: https://aistudio.google.com/app/apikey")
        print("  2. 创建 API key")
        print("  3. 设置环境变量:")
        print("     export GEMINI_API_KEY='your-key'")
        print("\n或者使用本地 Ollama:")
        print("   workflow = SCIResearchWorkflow(")
        print("       research_objective='优化 SCI',")
        print("       design_space=design_space,")
        print("       api_token='ollama',")
        print("       openapi_url='http://localhost:11434/v1/',")
        print("       llm_model='llama2'")
        print("   )")


def show_all_options():
    """显示所有初始化选项"""
    print("\n" + "="*70)
    print("📖 所有初始化选项")
    print("="*70)

    options = [
        ("完全自动（推荐）", """
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    budget_max=50
)
# 从环境变量自动读取"""),

        ("显式指定 Gemini", """
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    api_token="your-gemini-key",
    openapi_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    llm_model="gemini-2.0-flash-exp",
    llm_provider="openai"
)"""),

        ("使用 Anthropic", """
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    api_token="your-anthropic-key",
    llm_model="claude-sonnet-4-5",
    llm_provider="anthropic"
)"""),

        ("本地 Ollama", """
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI",
    design_space=design_space,
    api_token="ollama",
    openapi_url="http://localhost:11434/v1/",
    llm_model="llama2",
    llm_provider="openai"
)"""),
    ]

    for i, (name, code) in enumerate(options, 1):
        print(f"\n方式 {i}: {name}")
        print("-" * 70)
        print(code)


def main():
    """主函数"""
    print("\n" + "🔧 SCI Research Loop 配置助手")
    print("Version 2.1.0\n")

    # 检查环境
    has_config = check_environment()

    # 建议 provider
    suggest_provider()

    # 显示快速开始
    show_quick_start()

    # 显示所有选项
    show_all_options()

    # 最后的提示
    print("\n" + "="*70)
    print("📚 更多信息")
    print("="*70)
    print("- README: kosmos/ai_scientist/workflow/README.md")
    print("- 详细指南: kosmos/ai_scientist/workflow/INITIALIZATION_GUIDE.md")
    print("- 示例代码: examples/sci_workflow_with_openapi.py")
    print("="*70)

    # 返回状态
    if has_config:
        print("\n✅ 配置检查通过，可以开始使用!")
        return 0
    else:
        print("\n⚠️  请先配置 API key")
        return 1


if __name__ == "__main__":
    sys.exit(main())
