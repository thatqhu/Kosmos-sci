"""
测试 Configuration 哈希和去重功能
"""

import sys
sys.path.insert(0, '/home/qhu/workspace/Kosmos-sci')

from kosmos.ai_scientist.data_structures import Configuration


def test_configuration_hash():
    """测试配置哈希功能"""
    print("=" * 70)
    print("测试 1: Configuration 哈希功能")
    print("=" * 70)

    # 创建两个相同的配置
    config1 = Configuration(
        recon_family="CIAS-Core",
        uq_scheme="Conformal",
        recon_params={"layers": 10, "hidden_dim": 128},
        forward_config={"compression": 8},
        uq_params={"alpha": 0.1},
        train_config={"epochs": 50, "lr": 0.001}
    )

    config2 = Configuration(
        recon_family="CIAS-Core",
        uq_scheme="Conformal",
        recon_params={"layers": 10, "hidden_dim": 128},
        forward_config={"compression": 8},
        uq_params={"alpha": 0.1},
        train_config={"epochs": 50, "lr": 0.001}
    )

    # 测试哈希
    hash1 = config1.get_hash_key()
    hash2 = config2.get_hash_key()

    print(f"Config 1 hash: {hash1}")
    print(f"Config 2 hash: {hash2}")
    print(f"Hashes equal: {hash1 == hash2}")

    assert hash1 == hash2, "相同配置应该有相同的哈希"
    print("✓ 测试通过：相同配置生成相同哈希")

    # 测试相等性
    assert config1 == config2, "相同配置应该相等"
    print("✓ 测试通过：相等性判断正确")

    # 测试哈希函数
    assert hash(config1) == hash(config2), "__hash__ 应该相同"
    print("✓ 测试通过：__hash__ 方法正确")

    return True


def test_configuration_set():
    """测试配置可用于集合去重"""
    print("\n" + "=" * 70)
    print("测试 2: 配置集合去重")
    print("=" * 70)

    # 创建多个配置，其中有重复
    config_a = Configuration(
        recon_family="CIAS-Core",
        uq_scheme="Conformal",
        recon_params={"layers": 10},
        forward_config={},
        uq_params={},
        train_config={}
    )

    config_a_dup = Configuration(
        recon_family="CIAS-Core",
        uq_scheme="Conformal",
        recon_params={"layers": 10},
        forward_config={},
        uq_params={},
        train_config={}
    )

    config_b = Configuration(
        recon_family="CIAS-Core-ELP",
        uq_scheme="Ensemble",
        recon_params={"layers": 12},
        forward_config={},
        uq_params={},
        train_config={}
    )

    # 使用集合去重
    configs_set = {config_a, config_a_dup, config_b}

    print(f"原始配置数: 3")
    print(f"集合去重后: {len(configs_set)}")

    assert len(configs_set) == 2, "集合应该自动去重"
    print("✓ 测试通过：集合自动去重重复配置")

    return True


def test_different_configs():
    """测试不同配置生成不同哈希"""
    print("\n" + "=" * 70)
    print("测试 3: 不同配置的哈希")
    print("=" * 70)

    config1 = Configuration(
        recon_family="CIAS-Core",
        uq_scheme="Conformal",
        recon_params={"layers": 10},
        forward_config={},
        uq_params={},
        train_config={}
    )

    config2 = Configuration(
        recon_family="CIAS-Core-ELP",  # ← 不同
        uq_scheme="Conformal",
        recon_params={"layers": 10},
        forward_config={},
        uq_params={},
        train_config={}
    )

    config3 = Configuration(
        recon_family="CIAS-Core",
        uq_scheme="Ensemble",  # ← 不同
        recon_params={"layers": 10},
        forward_config={},
        uq_params={},
        train_config={}
    )

    hash1 = config1.get_hash_key()
    hash2 = config2.get_hash_key()
    hash3 = config3.get_hash_key()

    print(f"Config 1 (CIAS-Core + Conformal): {hash1}")
    print(f"Config 2 (CIAS-Core-ELP + Conformal): {hash2}")
    print(f"Config 3 (CIAS-Core + Ensemble): {hash3}")

    assert hash1 != hash2, "不同 recon_family 应该有不同哈希"
    assert hash1 != hash3, "不同 uq_scheme 应该有不同哈希"
    assert hash2 != hash3, "完全不同的配置应该有不同哈希"

    print("✓ 测试通过：不同配置生成不同哈希")

    return True


def test_parameter_order():
    """测试参数顺序不影响哈希"""
    print("\n" + "=" * 70)
    print("测试 4: 参数顺序无关性")
    print("=" * 70)

    # 参数顺序不同的两个配置
    config1 = Configuration(
        recon_family="CIAS-Core",
        uq_scheme="Conformal",
        recon_params={"a": 1, "b": 2, "c": 3},
        forward_config={},
        uq_params={},
        train_config={}
    )

    config2 = Configuration(
        recon_family="CIAS-Core",
        uq_scheme="Conformal",
        recon_params={"c": 3, "a": 1, "b": 2},  # ← 顺序不同
        forward_config={},
        uq_params={},
        train_config={}
    )

    hash1 = config1.get_hash_key()
    hash2 = config2.get_hash_key()

    print(f"Config 1 params: {config1.recon_params}")
    print(f"Config 2 params: {config2.recon_params}")
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")

    assert hash1 == hash2, "参数顺序不应该影响哈希"
    print("✓ 测试通过：参数顺序不影响哈希值")

    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("Configuration 哈希和去重功能测试")
    print("=" * 70)
    print()

    tests = {
        '哈希功能': test_configuration_hash,
        '集合去重': test_configuration_set,
        '不同配置': test_different_configs,
        '参数顺序': test_parameter_order,
    }

    results = {}
    for name, test_func in tests.items():
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"✗ {name} 失败: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

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
        print("\n🎉 所有测试通过！Configuration 哈希功能正常工作。")
        return 0
    else:
        print(f"\n⚠ {total - passed} 个测试失败。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
