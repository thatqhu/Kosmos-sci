"""
快速测试：验证多 LLM 提供商支持

测试 Planner 和 AnalysisAgent 是否正确支持多个提供商
"""

import os
import sys


def test_imports():
    """测试导入"""
    print("=" * 70)
    print("测试 1: 导入检查")
    print("=" * 70)

    try:
        from kosmos.ai_scientist.planner import Planner, OPENAI_AVAILABLE, ANTHROPIC_AVAILABLE
        from kosmos.ai_scientist.analysis import AnalysisAgent

        print(f"✓ OpenAI SDK: {'可用' if OPENAI_AVAILABLE else '不可用'}")
        print(f"✓ Anthropic SDK: {'可用' if ANTHROPIC_AVAILABLE else '不可用'}")

        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_planner_init():
    """测试 Planner 初始化支持多提供商"""
    print("\n" + "=" * 70)
    print("测试 2: Planner 多提供商支持")
    print("=" * 70)

    try:
        from kosmos.ai_scientist.planner import Planner

        # 测试无 API key
        planner1 = Planner()
        print(f"✓ 无 API key: provider={planner1.provider}")

        # 测试 OpenAI provider
        planner2 = Planner(
            api_key="fake-key",
            provider="openai",
            model="gemini-2.0-flash-exp"
        )
        print(f"✓ OpenAI provider: provider={planner2.provider}, model={planner2.model}")

        # 测试 Anthropic provider
        planner3 = Planner(
            api_key="fake-key",
            provider="anthropic",
            model="claude-sonnet-4-5"
        )
        print(f"✓ Anthropic provider: provider={planner3.provider}, model={planner3.model}")

        # 测试自动检测
        os.environ["GEMINI_API_KEY"] = "fake-gemini-key"
        planner4 = Planner(provider="auto")
        print(f"✓ Auto-detect (Gemini): provider={planner4.provider}")
        del os.environ["GEMINI_API_KEY"]

        return True
    except Exception as e:
        print(f"✗ Planner 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analysis_agent_init():
    """测试 AnalysisAgent 初始化支持多提供商"""
    print("\n" + "=" * 70)
    print("测试 3: AnalysisAgent 多提供商支持")
    print("=" * 70)

    try:
        from kosmos.ai_scientist.analysis import AnalysisAgent

        # 测试无 LLM 验证
        agent1 = AnalysisAgent(enable_llm_verification=False)
        print(f"✓ LLM 验证禁用: client={agent1.client}, provider={agent1.provider}")

        # 测试 OpenAI provider
        agent2 = AnalysisAgent(
            api_key="fake-key",
            provider="openai",
            model="gemini-2.0-flash-exp",
            enable_llm_verification=True
        )
        print(f"✓ OpenAI provider: provider={agent2.provider}, model={agent2.model}")

        # 测试 Anthropic provider
        agent3 = AnalysisAgent(
            api_key="fake-key",
            provider="anthropic",
            model="claude-sonnet-4-5",
            enable_llm_verification=True
        )
        print(f"✓ Anthropic provider: provider={agent3.provider}, model={agent3.model}")

        return True
    except Exception as e:
        print(f"✗ AnalysisAgent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_default_model():
    """测试默认模型是否改为 Gemini"""
    print("\n" + "=" * 70)
    print("测试 4: 默认模型检查")
    print("=" * 70)

    try:
        from kosmos.ai_scientist.planner import Planner
        from kosmos.ai_scientist.analysis import AnalysisAgent

        # Planner 默认模型
        planner = Planner(api_key="fake", provider="openai")
        assert planner.model == "gemini-2.0-flash-exp", f"Planner 默认模型错误: {planner.model}"
        print(f"✓ Planner 默认模型: {planner.model}")

        # AnalysisAgent 默认模型
        agent = AnalysisAgent(api_key="fake", provider="openai", enable_llm_verification=True)
        assert agent.model == "gemini-2.0-flash-exp", f"AnalysisAgent 默认模型错误: {agent.model}"
        print(f"✓ AnalysisAgent 默认模型: {agent.model}")

        return True
    except Exception as e:
        print(f"✗ 默认模型测试失败: {e}")
        return False


def test_parameter_compatibility():
    """测试参数向后兼容性"""
    print("\n" + "=" * 70)
    print("测试 5: 参数向后兼容性")
    print("=" * 70)

    try:
        from kosmos.ai_scientist.planner import Planner
        from kosmos.ai_scientist.analysis import AnalysisAgent

        # 旧式初始化 (v2.0) - 应该仍然工作
        planner_old = Planner(
            api_key="fake-key",
            model="claude-sonnet-4-5"
        )
        print(f"✓ 旧式 Planner 初始化: model={planner_old.model}")

        agent_old = AnalysisAgent(
            api_key="fake-key",
            model="claude-sonnet-4-5",
            enable_llm_verification=True
        )
        print(f"✓ 旧式 AnalysisAgent 初始化: model={agent_old.model}")

        # 新式初始化 (v2.1)
        planner_new = Planner(
            api_key="fake-key",
            provider="openai",
            model="gemini-2.0-flash-exp",
            base_url="https://custom.endpoint/"
        )
        print(f"✓ 新式 Planner 初始化: provider={planner_new.provider}")

        return True
    except Exception as e:
        print(f"✗ 兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("多 LLM 提供商支持 - 功能测试")
    print("=" * 70)
    print()

    results = {
        '导入检查': test_imports(),
        'Planner多提供商': test_planner_init(),
        'AnalysisAgent多提供商': test_analysis_agent_init(),
        '默认模型': test_default_model(),
        '向后兼容': test_parameter_compatibility(),
    }

    # 汇总
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} - {name}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！多 LLM 提供商支持已就绪。")
        print("\n下一步:")
        print("1. 安装依赖: pip install openai")
        print("2. 获取 Gemini API key: https://aistudio.google.com/app/apikey")
        print("3. 设置环境变量: export GEMINI_API_KEY=your-key")
        print("4. 运行示例: python3 examples/sci_workflow_gemini.py")
        return 0
    else:
        print(f"\n⚠ {total - passed} 个测试失败。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
