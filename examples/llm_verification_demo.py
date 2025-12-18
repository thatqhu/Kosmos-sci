"""
示例：使用LLM生成验证算法

演示如何使用AnalysisAgent的LLM功能来生成和执行自定义验证算法。
"""

import os
import asyncio
from kosmos.ai_scientist.analysis import AnalysisAgent
from kosmos.ai_scientist.planner import Planner
from kosmos.ai_scientist.data_structures import (
    ExperimentRecord,
    Configuration,
    Metrics,
    Artifacts
)


def create_sample_experiments():
    """创建示例实验数据用于测试。"""
    experiments = []

    # 实验 1: 高PSNR, 中等覆盖率
    exp1 = ExperimentRecord(
        id="exp1",
        config=Configuration(
            recon_family="CIAS-Core",
            uq_scheme="Conformal",
            forward_config={},
            recon_params={},
            uq_params={},
            train_config={}
        ),
        metrics=Metrics(psnr=35.5, coverage=0.85, latency=50.0),
        artifacts=Artifacts(checkpoint="", uq_params="", train_log="", eval_samples="", fig_scripts="")
    )
    experiments.append(exp1)

    # 实验 2: 中等PSNR, 高覆盖率
    exp2 = ExperimentRecord(
        id="exp2",
        config=Configuration(
            recon_family="CIAS-Core-ELP",
            uq_scheme="Ensemble",
            forward_config={},
            recon_params={},
            uq_params={},
            train_config={}
        ),
        metrics=Metrics(psnr=32.0, coverage=0.95, latency=55.0),
        artifacts=Artifacts(checkpoint="", uq_params="", train_log="", eval_samples="", fig_scripts="")
    )
    experiments.append(exp2)

    # 实验 3: 低PSNR, 低覆盖率 (被支配)
    exp3 = ExperimentRecord(
        id="exp3",
        config=Configuration(
            recon_family="Baseline-CNN",
            uq_scheme="None",
            forward_config={},
            recon_params={},
            uq_params={},
            train_config={}
        ),
        metrics=Metrics(psnr=28.0, coverage=0.75, latency=40.0),
        artifacts=Artifacts(checkpoint="", uq_params="", train_log="", eval_samples="", fig_scripts="")
    )
    experiments.append(exp3)

    # 实验 4: 最高PSNR, 低覆盖率
    exp4 = ExperimentRecord(
        id="exp4",
        config=Configuration(
            recon_family="CIAS-Core",
            uq_scheme="None",
            forward_config={},
            recon_params={},
            uq_params={},
            train_config={}
        ),
        metrics=Metrics(psnr=37.0, coverage=0.80, latency=45.0),
        artifacts=Artifacts(checkpoint="", uq_params="", train_log="", eval_samples="", fig_scripts="")
    )
    experiments.append(exp4)

    return experiments


def demo_planner_with_llm():
    """演示Planner的LLM功能。"""
    print("=" * 70)
    print("演示 1: Planner LLM初始化")
    print("=" * 70)

    # 方式 1: 自动从环境变量获取API key
    planner1 = Planner()
    print(f"✓ Planner创建成功 (client: {planner1.client is not None})")

    # 方式 2: 显式提供API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        planner2 = Planner(api_key=api_key, model="claude-sonnet-4-5")
        print(f"✓ Planner创建成功，使用模型: {planner2.model}")
    else:
        print("⚠ ANTHROPIC_API_KEY未设置，跳过API key测试")

    print()


def demo_analysis_with_llm():
    """演示AnalysisAgent的LLM验证功能。"""
    print("=" * 70)
    print("演示 2: AnalysisAgent LLM验证算法")
    print("=" * 70)

    # 创建示例数据
    experiments = create_sample_experiments()
    print(f"✓ 创建了 {len(experiments)} 个实验记录")

    for exp in experiments:
        print(f"  - {exp.id}: PSNR={exp.metrics.psnr:.1f}, Coverage={exp.metrics.coverage:.2f}")
    print()

    # 初始化AnalysisAgent (启用LLM验证)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ ANTHROPIC_API_KEY未设置，使用标准算法")
        analysis_agent = AnalysisAgent(enable_llm_verification=False)
    else:
        print("✓ 启用LLM验证功能")
        analysis_agent = AnalysisAgent(
            api_key=api_key,
            model="claude-sonnet-4-5",
            enable_llm_verification=True
        )

    # 比较标准算法和LLM生成的算法
    print("\n--- 标准Pareto前沿算法 ---")
    standard_pareto = AnalysisAgent.compute_pareto_front(experiments, objectives=['psnr', 'coverage'])
    print(f"Pareto前沿: {standard_pareto}")

    if analysis_agent.enable_llm_verification and analysis_agent.client:
        print("\n--- LLM生成的验证算法 ---")
        llm_pareto, code = analysis_agent.verify_pareto_with_llm(experiments, objectives=['psnr', 'coverage'])

        if llm_pareto:
            print(f"Pareto前沿: {llm_pareto}")
            print(f"\n生成的代码 ({len(code)} 字符):")
            print("-" * 70)
            print(code)
            print("-" * 70)

            # 比较结果
            if standard_pareto == llm_pareto:
                print("\n✓ LLM生成的算法与标准算法结果一致！")
            else:
                print(f"\n⚠ 结果不同:")
                print(f"  标准: {standard_pareto}")
                print(f"  LLM:  {llm_pareto}")
                print(f"  差异: {standard_pareto.symmetric_difference(llm_pareto)}")
        else:
            print("✗ LLM验证失败，回退到标准算法")
    else:
        print("\n⚠ LLM验证未启用")

    print()


def demo_custom_verification():
    """演示自定义验证任务。"""
    print("=" * 70)
    print("演示 3: 自定义验证任务")
    print("=" * 70)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ ANTHROPIC_API_KEY未设置，跳过此演示")
        return

    # 创建示例数据
    experiments = create_sample_experiments()

    # 初始化AnalysisAgent
    analysis_agent = AnalysisAgent(
        api_key=api_key,
        enable_llm_verification=True
    )

    # 自定义任务：找出延迟最低的前3个实验
    task = "Find the top 3 experiments with lowest latency"
    context = {
        'description': """
        Given a list of experiments, identify the 3 experiments with the lowest latency.
        Return a list of experiment IDs sorted by latency (ascending).
        """
    }

    print(f"任务: {task}")
    code = analysis_agent.generate_verification_algorithm(task, context)

    if code:
        print(f"\n生成的代码:")
        print("-" * 70)
        print(code)
        print("-" * 70)

        # 执行代码
        result = analysis_agent.execute_verification_code(code, experiments)
        if result:
            print(f"\n结果: {result}")

            # 验证结果
            sorted_by_latency = sorted(experiments, key=lambda e: e.metrics.latency)[:3]
            expected = [e.id for e in sorted_by_latency]
            print(f"期望: {expected}")

            if list(result) == expected:
                print("✓ 结果正确！")
            else:
                print("⚠ 结果与预期不同")
        else:
            print("✗ 代码执行失败")
    else:
        print("✗ 代码生成失败")

    print()


def main():
    """主函数：运行所有演示。"""
    print("\n" + "=" * 70)
    print("LLM验证算法演示")
    print("=" * 70 + "\n")

    # 检查API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"✓ ANTHROPIC_API_KEY已设置 (长度: {len(api_key)})")
    else:
        print("⚠ ANTHROPIC_API_KEY未设置，某些功能将被禁用")
        print("  设置方法: export ANTHROPIC_API_KEY=your-api-key")
    print()

    # 运行演示
    demo_planner_with_llm()
    demo_analysis_with_llm()
    demo_custom_verification()

    print("=" * 70)
    print("演示完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
