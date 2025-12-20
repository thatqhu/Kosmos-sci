#!/usr/bin/env python3
"""
测试示例: 使用 Mock Training Service

演示 Executor 如何调用 Mock Training Service 进行训练
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kosmos.ai_scientist.executor import Executor
from kosmos.ai_scientist.data_structures import Configuration


def test_executor_with_service():
    """测试 Executor 调用 Mock Training Service"""

    print("="*70)
    print("测试: Executor with Mock Training Service")
    print("="*70)

    # 创建测试配置
    config1 = Configuration(
        recon_family="CIAS-Core-ELP",
        recon_params={"num_layers": 10, "hidden_dim": 128},
        uq_scheme="Conformal",
        uq_params={"alpha": 0.1},
        forward_config={"compression_ratio": 8},
        train_config={"epochs": 50, "lr": 0.001}
    )

    config2 = Configuration(
        recon_family="CIAS-Core",
        recon_params={"num_layers": 8, "hidden_dim": 64},
        uq_scheme="Ensemble",
        uq_params={"n_models": 5},
        forward_config={"compression_ratio": 16},
        train_config={"epochs": 40, "lr": 0.0005}
    )

    config3 = Configuration(
        recon_family="Baseline-CNN",
        recon_params={"num_layers": 6},
        uq_scheme="None",
        uq_params={},
        forward_config={"compression_ratio": 8},
        train_config={"epochs": 30, "lr": 0.001}
    )

    configs = [config1, config2, config3]

    # 创建 Executor (会自动检测服务)
    print("\n1. 创建 Executor...")
    executor = Executor(
        service_url="http://localhost:8001",
        use_mock_service=True
    )

    print(f"   Service available: {executor.service_available}")
    print(f"   Service URL: {executor.service_url}")

    # 运行实验
    print("\n2. 运行实验...")
    results = []

    for i, config in enumerate(configs, 1):
        print(f"\n   实验 {i}/{len(configs)}")
        print(f"   Config: {config.recon_family} + {config.uq_scheme}")

        try:
            metrics, artifacts = executor.run_campaign(config)

            print(f"   ✅ 完成!")
            print(f"      PSNR: {metrics.psnr:.2f} dB")
            print(f"      Coverage: {metrics.coverage:.2%}")
            print(f"      Latency: {metrics.latency:.1f} ms")
            if metrics.calibration_error:
                print(f"      Calibration Error: {metrics.calibration_error:.4f}")

            results.append({
                'config': config,
                'metrics': metrics,
                'artifacts': artifacts
            })

        except Exception as e:
            print(f"   ❌ 失败: {e}")

    # 结果汇总
    print("\n" + "="*70)
    print("结果汇总")
    print("="*70)
    print(f"总实验数: {len(results)}")

    if results:
        best = max(results, key=lambda r: r['metrics'].psnr)
        print(f"\n最优配置:")
        print(f"  Recon Family: {best['config'].recon_family}")
        print(f"  UQ Scheme: {best['config'].uq_scheme}")
        print(f"  PSNR: {best['metrics'].psnr:.2f} dB")
        print(f"  Coverage: {best['metrics'].coverage:.2%}")

    return len(results) > 0


def test_executor_without_service():
    """测试 Executor 在没有服务时使用本地 mock"""

    print("\n" + "="*70)
    print("测试: Executor without Service (Local Mock)")
    print("="*70)

    # 创建 Executor (禁用服务)
    executor = Executor(use_mock_service=False)

    print(f"Service available: {executor.service_available}")

    # 创建配置
    config = Configuration(
        recon_family="CIAS-Core-ELP",
        recon_params={"num_layers": 10},
        uq_scheme="Conformal",
        uq_params={"alpha": 0.1},
        forward_config={},
        train_config={"epochs": 50}
    )

    print("\n运行实验 (Local Mock)...")
    metrics, artifacts = executor.run_campaign(config)

    print(f"✅ 完成!")
    print(f"   PSNR: {metrics.psnr:.2f} dB")
    print(f"   Coverage: {metrics.coverage:.2%}")
    print(f"   Checkpoint: {artifacts.checkpoint}")


def main():
    """主函数"""
    print("\n🧪 Executor 测试\n")

    # 测试 1: 使用服务
    print("🔍 检查 Mock Training Service...")

    try:
        import requests
        response = requests.get("http://localhost:8001/health", timeout=2)
        if response.status_code == 200:
            print("✅ Mock Training Service 正在运行")
            success1 = test_executor_with_service()
        else:
            print("⚠️  Mock Training Service 响应异常")
            success1 = False
    except Exception as e:
        print("⚠️  Mock Training Service 未启动")
        print("   请先运行: ./scripts/start_mock_service.sh")
        print("   或者: python3 tests/mock_training_service.py")
        success1 = False

    # 测试 2: 本地 mock
    success2 = test_executor_without_service()

    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    print(f"Service Mode: {'✅ 通过' if success1 else '⚠️  跳过 (服务未启动)'}")
    print(f"Local Mock Mode: ✅ 通过")

    if not success1:
        print("\n💡 提示: 启动 Mock Training Service 以测试完整功能")
        print("   ./scripts/start_mock_service.sh")

    return success2


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
