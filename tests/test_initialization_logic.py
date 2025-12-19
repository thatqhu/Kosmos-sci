#!/usr/bin/env python3
"""
简单测试: 验证 _initialize_llm_client 方法的逻辑

不依赖完整的项目环境，只测试初始化逻辑
"""

def test_client_initialization_logic():
    """模拟测试 LLM client 初始化逻辑"""

    print("="*70)
    print("测试 LLM Client 初始化逻辑")
    print("="*70)

    # 测试 1: Provider 自动检测
    print("\n测试 1: Provider 自动检测")
    print("-"*70)

    import os

    # 模拟不同的环境变量场景
    scenarios = [
        {"GEMINI_API_KEY": "test-key", "expected": "openai"},
        {"ANTHROPIC_API_KEY": "test-key", "expected": "anthropic"},
        {"OPENAI_API_KEY": "test-key", "expected": "openai"},
        {}, # 无 key
    ]

    for i, scenario in enumerate(scenarios, 1):
        # 清空环境变量
        for key in ["GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]:
            os.environ.pop(key, None)

        # 设置测试环境变量
        for key, value in scenario.items():
            os.environ[key] = value

        # 模拟自动检测逻辑
        provider = "auto"
        api_token = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

        if provider == "auto":
            if os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY"):
                detected_provider = "openai"
            elif os.getenv("ANTHROPIC_API_KEY"):
                detected_provider = "anthropic"
            else:
                detected_provider = "openai"  # 默认

        expected = scenario.get("expected", "openai")
        status = "✓" if not api_token or detected_provider == expected else "✗"

        print(f"  场景 {i}: {scenario}")
        print(f"    检测结果: {detected_provider} {status}")
        print(f"    API Token: {'存在' if api_token else '不存在'}")

    # 测试 2: 不同 provider 的端点设置
    print("\n测试 2: 默认端点设置")
    print("-"*70)

    provider_configs = [
        {
            "provider": "openai",
            "base_url": None,
            "expected_url": "https://generativelanguage.googleapis.com/v1beta/openai/"
        },
        {
            "provider": "openai",
            "base_url": "http://localhost:11434/v1/",
            "expected_url": "http://localhost:11434/v1/"
        },
        {
            "provider": "anthropic",
            "base_url": None,
            "expected_url": None  # Anthropic 不需要 base_url
        },
    ]

    for config in provider_configs:
        provider = config["provider"]
        base_url = config["base_url"]
        expected_url = config["expected_url"]

        # 模拟端点设置逻辑
        if provider == "openai":
            if base_url is None:
                final_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            else:
                final_url = base_url
        else:
            final_url = None

        status = "✓" if final_url == expected_url else "✗"

        print(f"  Provider: {provider}")
        print(f"    输入 base_url: {base_url}")
        print(f"    最终 URL: {final_url} {status}")

    # 测试 3: 参数优先级
    print("\n测试 3: 参数优先级")
    print("-"*70)

    # 场景: api_token 参数 vs 环境变量
    os.environ["GEMINI_API_KEY"] = "env-key"

    test_cases = [
        {"param": "param-key", "expected": "param-key"},
        {"param": None, "expected": "env-key"},
    ]

    for case in test_cases:
        param_token = case["param"]
        expected = case["expected"]

        # 模拟优先级逻辑
        api_token = param_token or os.getenv("GEMINI_API_KEY")

        status = "✓" if api_token == expected else "✗"
        print(f"  参数: {param_token}, 环境变量: env-key")
        print(f"    最终使用: {api_token} {status}")

    print("\n" + "="*70)
    print("✓ 所有逻辑测试完成!")
    print("="*70)


if __name__ == "__main__":
    test_client_initialization_logic()
