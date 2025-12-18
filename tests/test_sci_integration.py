"""
测试脚本：验证 SCI Research Loop 的所有功能

这个脚本测试：
1. 基本初始化
2. LLM 功能（如果可用）
3. Kosmos 集成接口
"""

import os
import sys


def test_imports():
    """测试所有导入是否正常"""
    print("=" * 70)
    print("测试 1: 导入检查")
    print("=" * 70)

    try:
        from kosmos.ai_scientist.workflow import SCIResearchWorkflow
        print("✓ SCIResearchWorkflow 导入成功")

        from kosmos.ai_scientist.planner import Planner
        print("✓ Planner 导入成功")

        from kosmos.ai_scientist.analysis import AnalysisAgent
        print("✓ AnalysisAgent 导入成功")

        from kosmos.ai_scientist.data_structures import (
            Configuration, ExperimentRecord, Metrics, Artifacts
        )
        print("✓ 数据结构导入成功")

        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_planner_initialization():
    """测试 Planner 初始化"""
    print("\n" + "=" * 70)
    print("测试 2: Planner 初始化")
    print("=" * 70)

    try:
        from kosmos.ai_scientist.planner import Planner

        # 测试无 API key 初始化
        planner1 = Planner()
        print(f"✓ Planner 创建成功 (client: {planner1.client is not None})")

        # 测试带 API key 初始化
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            planner2 = Planner(api_key=api_key)
            print(f"✓ Planner with API key 创建成功 (model: {planner2.model})")
        else:
            print("⚠ ANTHROPIC_API_KEY 未设置，跳过 API key 测试")

        # 测试 planner_step 方法存在
        assert hasattr(planner1, 'planner_step'), "缺少 planner_step 方法"
        assert hasattr(planner1, 'llm_generate_configs'), "缺少 llm_generate_configs 方法"
        print("✓ Planner 方法检查通过")

        return True
    except Exception as e:
        print(f"✗ Planner 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analysis_initialization():
    """测试 AnalysisAgent 初始化"""
    print("\n" + "=" * 70)
    print("测试 3: AnalysisAgent 初始化")
    print("=" * 70)

    try:
        from kosmos.ai_scientist.analysis import AnalysisAgent

        # 测试无 LLM 初始化
        analysis1 = AnalysisAgent(enable_llm_verification=False)
        print(f"✓ AnalysisAgent 创建成功 (LLM: {analysis1.enable_llm_verification})")

        # 测试带 LLM 初始化
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            analysis2 = AnalysisAgent(
                api_key=api_key,
                enable_llm_verification=True
            )
            print(f"✓ AnalysisAgent with LLM 创建成功 (client: {analysis2.client is not None})")
        else:
            print("⚠ ANTHROPIC_API_KEY 未设置，跳过 LLM 测试")

        # 测试方法存在
        assert hasattr(analysis1, 'analysis_step'), "缺少 analysis_step 方法"
        assert hasattr(analysis1, 'generate_verification_algorithm'), "缺少 generate_verification_algorithm 方法"
        assert hasattr(analysis1, 'verify_pareto_with_llm'), "缺少 verify_pareto_with_llm 方法"
        print("✓ AnalysisAgent 方法检查通过")

        return True
    except Exception as e:
        print(f"✗ AnalysisAgent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_initialization():
    """测试 SCIResearchWorkflow 初始化"""
    print("\n" + "=" * 70)
    print("测试 4: SCIResearchWorkflow 初始化")
    print("=" * 70)

    try:
        from kosmos.ai_scientist.workflow import SCIResearchWorkflow

        # 创建简单的设计空间
        design_space = {
            'recon_families': ['CIAS-Core', 'CIAS-Core-ELP'],
            'uq_schemes': ['Conformal', 'None']
        }

        # 测试基本初始化
        workflow = SCIResearchWorkflow(
            research_objective="Test",
            design_space=design_space,
            budget_max=10
        )

        print(f"✓ SCIResearchWorkflow 创建成功")
        print(f"  - Planner: {workflow.planner is not None}")
        print(f"  - AnalysisAgent: {workflow.analysis_agent is not None}")
        print(f"  - StateManager: {workflow.state_manager is not None}")
        print(f"  - Executor: {workflow.executor is not None}")

        return True
    except Exception as e:
        print(f"✗ Workflow 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_kosmos_interface():
    """测试 Kosmos 集成接口"""
    print("\n" + "=" * 70)
    print("测试 5: Kosmos 集成接口")
    print("=" * 70)

    try:
        from kosmos.ai_scientist.workflow import SCIResearchWorkflow

        design_space = {
            'recon_families': ['CIAS-Core'],
            'uq_schemes': ['None']
        }

        workflow = SCIResearchWorkflow(
            research_objective="Test",
            design_space=design_space,
            budget_max=10
        )

        # 检查所有接口方法
        required_methods = [
            'get_cycle_context',
            'to_research_finding',
            'get_all_findings_as_research_format',
            'get_statistics',
            'generate_report'
        ]

        for method in required_methods:
            assert hasattr(workflow, method), f"缺少方法: {method}"
            print(f"  ✓ {method}")

        # 测试 get_statistics
        stats = workflow.get_statistics()
        assert 'workflow' in stats, "statistics 缺少 'workflow'"
        assert 'planner' in stats, "statistics 缺少 'planner'"
        assert 'analysis' in stats, "statistics 缺少 'analysis'"
        print(f"\n✓ get_statistics() 返回正确结构")
        print(f"  - Workflow type: {stats['workflow']['type']}")
        print(f"  - LLM enabled: {stats['planner']['llm_enabled']}")

        return True
    except Exception as e:
        print(f"✗ 接口测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_structures():
    """测试数据结构"""
    print("\n" + "=" * 70)
    print("测试 6: 数据结构")
    print("=" * 70)

    try:
        from kosmos.ai_scientist.data_structures import (
            Configuration, ExperimentRecord, Metrics, Artifacts
        )

        # 创建测试配置
        config = Configuration(
            recon_family="CIAS-Core",
            uq_scheme="Conformal",
            forward_config={},
            recon_params={},
            uq_params={},
            train_config={}
        )
        print("✓ Configuration 创建成功")

        # 创建测试指标
        metrics = Metrics(
            psnr=35.5,
            coverage=0.85,
            latency=50.0
        )
        print("✓ Metrics 创建成功")

        # 创建测试 artifacts
        artifacts = Artifacts(
            checkpoint="",
            uq_params="",
            train_log="",
            eval_samples="",
            fig_scripts=""
        )
        print("✓ Artifacts 创建成功")

        # 创建实验记录
        experiment = ExperimentRecord(
            id="test_exp",
            config=config,
            metrics=metrics,
            artifacts=artifacts
        )
        print("✓ ExperimentRecord 创建成功")

        # 测试 to_dict 方法
        config_dict = config.to_dict()
        assert 'recon_family' in config_dict
        print("✓ to_dict() 方法正常")

        return True
    except Exception as e:
        print(f"✗ 数据结构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("SCI Research Loop 功能测试")
    print("=" * 70)

    # 检查 API key 状态
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"\n✓ ANTHROPIC_API_KEY 已设置 (长度: {len(api_key)})")
    else:
        print("\n⚠ ANTHROPIC_API_KEY 未设置，部分功能将被跳过")
        print("  设置方法: export ANTHROPIC_API_KEY=your-api-key\n")

    # 运行测试
    results = {
        '导入检查': test_imports(),
        'Planner初始化': test_planner_initialization(),
        'AnalysisAgent初始化': test_analysis_initialization(),
        'Workflow初始化': test_workflow_initialization(),
        'Kosmos接口': test_kosmos_interface(),
        '数据结构': test_data_structures()
    }

    # 汇总结果
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
        print("\n🎉 所有测试通过！系统已准备好独立运行和 Kosmos 集成。")
        return 0
    else:
        print(f"\n⚠ {total - passed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
