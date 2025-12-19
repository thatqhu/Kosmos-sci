#!/usr/bin/env python3
"""
快速测试: 验证 SCIResearchWorkflow 的新初始化逻辑

测试不同的初始化方式是否正常工作
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kosmos.ai_scientist.workflow.sci_research_loop import SCIResearchWorkflow


def test_initialization():
    """测试各种初始化方式"""

    design_space = {
        "recon_families": ["CIAS-Core"],
        "uq_schemes": ["None"],
    }

    print("="*70)
    print("测试 1: 无 API token (应该警告)")
    print("="*70)

    workflow1 = SCIResearchWorkflow(
        research_objective="测试1",
        design_space=design_space,
        budget_max=5
    )

    print(f"✓ 工作流创建成功")
    print(f"  LLM Client: {workflow1.llm_client}")
    print(f"  Planner Provider: {workflow1.planner.provider}")


    print("\n" + "="*70)
    print("测试 2: 使用显式 API token (模拟)")
    print("="*70)

    workflow2 = SCIResearchWorkflow(
        research_objective="测试2",
        design_space=design_space,
        api_token="test-token-123",
        openapi_url="http://localhost:8000/v1/",
        llm_model="test-model",
        llm_provider="openai",
        budget_max=5
    )

    print(f"✓ 工作流创建成功")
    print(f"  LLM Client: {type(workflow2.llm_client).__name__ if workflow2.llm_client else None}")
    print(f"  Planner Provider: {workflow2.planner.provider}")


    print("\n" + "="*70)
    print("测试 3: 从环境变量加载 (如果存在)")
    print("="*70)

    # 检查环境变量
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    print(f"环境变量状态:")
    print(f"  GEMINI_API_KEY: {'✓ 已设置' if has_gemini else '✗ 未设置'}")
    print(f"  ANTHROPIC_API_KEY: {'✓ 已设置' if has_anthropic else '✗ 未设置'}")
    print(f"  OPENAI_API_KEY: {'✓ 已设置' if has_openai else '✗ 未设置'}")

    if has_gemini or has_anthropic or has_openai:
        workflow3 = SCIResearchWorkflow(
            research_objective="测试3",
            design_space=design_space,
            llm_provider="auto",
            budget_max=5
        )

        print(f"\n✓ 工作流创建成功")
        print(f"  LLM Client: {type(workflow3.llm_client).__name__ if workflow3.llm_client else None}")
        print(f"  Planner Provider: {workflow3.planner.provider}")
        print(f"  Planner Model: {workflow3.planner.model}")
    else:
        print("\n⚠️ 未找到任何 API key 环境变量，跳过此测试")


    print("\n" + "="*70)
    print("测试 4: 属性检查")
    print("="*70)

    workflow4 = SCIResearchWorkflow(
        research_objective="测试4",
        design_space=design_space,
        api_token="dummy",
        budget_max=10
    )

    # 检查所有必需的属性
    attributes = [
        'research_objective',
        'design_space',
        'budget_max',
        'llm_client',
        'state_manager',
        'executor',
        'planner',
        'analysis_agent'
    ]

    for attr in attributes:
        has_attr = hasattr(workflow4, attr)
        value = getattr(workflow4, attr, None)
        print(f"  {attr}: {'✓' if has_attr else '✗'} (type: {type(value).__name__})")


    print("\n" + "="*70)
    print("✓ 所有测试完成!")
    print("="*70)

    return True


if __name__ == "__main__":
    try:
        success = test_initialization()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
