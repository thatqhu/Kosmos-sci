# Configuration 去重优化

## 📋 更新说明

**日期**: 2025-12-18
**版本**: v2.2 - Configuration Deduplication

---

## 🎯 问题

在之前的实现中，LLM 可能会生成已经尝试过的配置，导致：
- 浪费实验预算
- 重复运行相同的实验
- 降低探索效率

---

## ✅ 解决方案

### 1. **为 Configuration 添加哈希功能**

**文件**: `kosmos/ai_scientist/data_structures.py`

```python
@dataclass
class Configuration:
    # ... 原有字段 ...

    def get_hash_key(self) -> str:
        """
        生成唯一的哈希键。

        使用 SHA256 对配置的规范化 JSON 表示进行哈希。
        相同的配置总是生成相同的哈希。
        """
        import json
        import hashlib

        # 创建规范化表示（排序键）
        config_dict = {
            'recon_family': self.recon_family,
            'recon_params': self._dict_to_sorted_str(self.recon_params),
            'uq_scheme': self.uq_scheme,
            'uq_params': self._dict_to_sorted_str(self.uq_params),
            'forward_config': self._dict_to_sorted_str(self.forward_config),
            'train_config': self._dict_to_sorted_str(self.train_config)
        }

        canonical_str = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(canonical_str.encode()).hexdigest()[:16]

    def __hash__(self) -> int:
        """使 Configuration 可用于 set 和 dict"""
        return int(self.get_hash_key(), 16)

    def __eq__(self, other) -> bool:
        """基于哈希键判断相等性"""
        if not isinstance(other, Configuration):
            return False
        return self.get_hash_key() == other.get_hash_key()
```

**关键特性**:
- ✅ 规范化表示（排序字典键）
- ✅ SHA256 哈希（前16位）
- ✅ 可用于 `set()` 和 `dict` 键
- ✅ 两个相同配置总是哈希相同

---

### 2. **Planner 添加去重逻辑**

**文件**: `kosmos/ai_scientist/planner.py`

```python
def planner_step(
    self,
    summary: Dict[str, Any],
    design_space: Dict[str, List[Any]],
    budget_remaining: int,
    explored_configs: Optional[List[Configuration]] = None  # ← 新增参数
) -> List[Configuration]:
    """
    规划步骤，现在支持配置去重。
    """
    # 1. 构建已探索配置的哈希集合（O(1) 查找）
    explored_hashes = set()
    if explored_configs:
        for config in explored_configs:
            explored_hashes.add(config.get_hash_key())

    logger.info(f"[Planner] {len(explored_hashes)} configurations already explored")

    # 2. 生成 LLM 提案
    proposals_raw = self.llm_generate_configs(prompt)

    # 3. 过滤重复配置
    new_configs = []
    duplicate_count = 0

    for proposal in proposals_raw:
        config = Planner.project_to_design_space(proposal, design_space)
        config_hash = config.get_hash_key()

        # 检查是否重复
        if config_hash in explored_hashes:
            duplicate_count += 1
            logger.debug(f"[Planner] Skipping duplicate: {config.recon_family}")
            continue  # ← 跳过重复配置

        # 验证并添加
        if Planner.is_valid_config(config, constraints):
            new_configs.append(config)
            explored_hashes.add(config_hash)  # 标记为已用

    logger.info(
        f"[Planner] Generated {len(new_configs)} new configs "
        f"({duplicate_count} duplicates filtered)"
    )

    return new_configs
```

---

### 3. **SCIResearchWorkflow 传递探索历史**

**文件**: `kosmos/ai_scientist/workflow/sci_research_loop.py`

```python
def _simple_planning(
    self,
    context: Dict,
    num_experiments: int
) -> List[Configuration]:
    """实验规划，现在支持去重。"""

    # 1. 从上下文获取已探索配置（字典格式）
    explored_configs_dict = context.get('explored_configs', [])

    # 2. 转换为 Configuration 对象
    explored_config_objects = []
    for config_dict in explored_configs_dict:
        config_obj = Configuration(
            recon_family=config_dict.get('recon_family', ''),
            uq_scheme=config_dict.get('uq_scheme', ''),
            recon_params=config_dict.get('recon_params', {}),
            # ... 其他字段
        )
        explored_config_objects.append(config_obj)

    # 3. 调用 Planner，传入已探索配置
    configs = self.planner.planner_step(
        summary,
        self.design_space,
        budget,
        explored_configs=explored_config_objects  # ← 传递用于去重
    )

    return configs
```

---

## 📊 工作流程

```
周期 1:
  explored_configs = []  (空)
  LLM 生成: [Config A, Config B, Config C]
  去重后: [Config A, Config B, Config C]  (3个新配置)
  执行实验

周期 2:
  explored_configs = [A, B, C]
  explored_hashes = {hash(A), hash(B), hash(C)}

  LLM 生成: [Config D, Config A, Config E]  (A 重复了!)
  去重过程:
    - Config D: hash(D) not in explored_hashes ✓ 添加
    - Config A: hash(A) in explored_hashes ✗ 跳过 (duplicate!)
    - Config E: hash(E) not in explored_hashes ✓ 添加

  去重后: [Config D, Config E]  (2个新配置, 1个重复)
  日志: "Generated 2 new configs (1 duplicates filtered)"
  执行实验

周期 3:
  explored_configs = [A, B, C, D, E]
  explored_hashes = {hash(A), hash(B), hash(C), hash(D), hash(E)}

  LLM 生成: [Config F, Config B, Config G, Config D]
  去重后: [Config F, Config G]  (2个新配置, 2个重复)
  日志: "Generated 2 new configs (2 duplicates filtered)"
  ...
```

---

## 🎯 优势

### 1. **避免重复实验**
```python
# 之前：可能重复
Cycle 1: 运行 Config A (PSNR=35dB)
Cycle 5: 又运行 Config A ← 浪费!

# 现在：自动跳过
Cycle 1: 运行 Config A (PSNR=35dB)
Cycle 5: LLM 建议 Config A
         → 检测到重复 → 跳过 ✓
```

### 2. **节省预算**
```python
# 50 个实验预算

# 之前：可能浪费 10-20%
实际新配置: 40-45 个

# 现在：充分利用
实际新配置: ~50 个 (最大化探索)
```

### 3. **提高探索效率**
- 每个实验都是新的探索
- 不会在相同配置上重复花费时间
- 更快找到最优解

### 4. **O(1) 性能**
```python
# 使用哈希集合
if config_hash in explored_hashes:  # ← O(1) 查找
    skip

# 而不是遍历
for explored in explored_configs:  # ← O(n) 查找
    if config == explored:
        skip
```

---

## 🔍 哈希碰撞处理

### **概率分析**

```python
# SHA256 的 16 位十六进制 = 64 bits
可能的哈希值: 2^64 ≈ 1.8 × 10^19

# 生日悖论：50% 碰撞概率需要
n ≈ √(2^64) ≈ 4.3 × 10^9 个配置

# SCI 实验场景:
典型实验数: 50-1000 个
碰撞概率: < 10^-12 (几乎不可能)
```

**结论**: 在实际使用中，哈希碰撞的概率可以忽略不计。

---

## 📈 示例输出

```bash
[Planner] 15 configurations already explored

[LLM Planner] Generating configurations with gemini-2.0-flash-exp (provider: openai)
[LLM Planner] Response received: 2847 chars
[LLM Planner] Generated 5 proposals

[Planner] Skipping duplicate: CIAS-Core + Conformal
[Planner] Skipping duplicate: CIAS-Core-ELP + Ensemble

[Planner] Generated 3 new configs (2 duplicates filtered)

Planner proposed 3 new configurations
```

---

## 🧪 测试

### 测试哈希功能

```python
from kosmos.ai_scientist.data_structures import Configuration

# 创建两个相同的配置
config1 = Configuration(
    recon_family="CIAS-Core",
    uq_scheme="Conformal",
    recon_params={"layers": 10},
    forward_config={},
    uq_params={},
    train_config={}
)

config2 = Configuration(
    recon_family="CIAS-Core",
    uq_scheme="Conformal",
    recon_params={"layers": 10},
    forward_config={},
    uq_params={},
    train_config={}
)

# 测试哈希
assert config1.get_hash_key() == config2.get_hash_key()  # ✓ 相同哈希
assert config1 == config2  # ✓ 相等
assert hash(config1) == hash(config2)  # ✓ 可用于集合

# 测试集合去重
configs = {config1, config2}
assert len(configs) == 1  # ✓ 自动去重
```

### 测试去重功能

```python
from kosmos.ai_scientist.planner import Planner

planner = Planner()

# 已探索的配置
explored = [config1, config2, config3]

# 调用 planner（会自动去重）
new_configs = planner.planner_step(
    summary=summary,
    design_space=design_space,
    budget_remaining=5,
    explored_configs=explored  # ← 传入已探索配置
)

# 验证没有重复
for config in new_configs:
    assert config not in explored  # ✓ 都是新配置
```

---

## 🎓 技术要点

### 1. **规范化很重要**

```python
# 错误的哈希方式（顺序影响）
{"a": 1, "b": 2}  → hash_1
{"b": 2, "a": 1}  → hash_2 (不同!)

# 正确的哈希方式（排序键）
json.dumps({"a": 1, "b": 2}, sort_keys=True)
json.dumps({"b": 2, "a": 1}, sort_keys=True)
# 两者生成相同的 JSON → 相同的哈希 ✓
```

### 2. **嵌套字典处理**

```python
def _dict_to_sorted_str(self, d: Dict) -> str:
    """递归排序嵌套字典"""
    return json.dumps(d, sort_keys=True)

# 确保嵌套结构也被正确哈希
config.recon_params = {
    "conv": {"layers": 10},
    "dense": {"units": 128}
}
# → 排序后生成确定性字符串
```

### 3. **集合操作优势**

```python
# 使用集合（O(1)）
explored_hashes = {hash1, hash2, hash3, ...}  # set
if new_hash in explored_hashes:  # O(1)
    skip

# 对比列表（O(n)）
explored_configs = [config1, config2, config3, ...]  # list
for exp in explored_configs:  # O(n)
    if new_config == exp:
        skip
```

---

## 🔄 向后兼容

```python
# 旧代码仍然工作（explored_configs 是可选的）
configs = planner.planner_step(summary, design_space, budget)
# → 不传 explored_configs，不会去重（但不会报错）

# 新代码（启用去重）
configs = planner.planner_step(
    summary, design_space, budget,
    explored_configs=explored_list  # ← 可选参数
)
# → 传了 explored_configs，会自动去重
```

---

## 📝 总结

**改进点**:
1. ✅ Configuration 支持哈希和相等性比较
2. ✅ Planner 自动过滤重复配置
3. ✅ SCIResearchWorkflow 传递探索历史
4. ✅ O(1) 性能，高效去重
5. ✅ 向后兼容，旧代码不受影响

**效果**:
- 避免重复实验
- 节省实验预算
- 提高探索效率
- 更快收敛到最优解

**代码变更**:
- `data_structures.py`: +45 行
- `planner.py`: +30 行
- `sci_research_loop.py`: +20 行
- **总计**: ~95 行新代码

---

**版本**: v2.2
**日期**: 2025-12-18
**状态**: ✅ 已完成并测试
