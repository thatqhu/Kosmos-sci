# Mock Training Service 使用指南

## 概述

Mock Training Service 是一个基于 FastAPI 的测试服务，用于模拟 SCI 重建模型的训练过程。它返回随机但合理的训练结果，用于测试 Executor 和整个工作流。

## 架构

```
┌─────────────────┐         HTTP POST          ┌──────────────────────────┐
│                 │    /train (JSON)            │                          │
│   Executor      ├────────────────────────────>│  Mock Training Service   │
│                 │                             │                          │
│  (executor.py)  │<────────────────────────────┤   (FastAPI on :8001)     │
│                 │    Response (JSON)          │                          │
└─────────────────┘                             └──────────────────────────┘
       │                                                    │
       │ Fallback                                          │
       v (if service unavailable)                          v
┌─────────────────┐                             ┌──────────────────────────┐
│  Local Mock     │                             │  Simulated Training      │
│                 │                             │  - Random PSNR/Coverage  │
│  Simple Random  │                             │  - Based on config       │
└─────────────────┘                             │  - Realistic artifacts   │
                                                └──────────────────────────┘
```

## 快速开始

### 1️⃣ 启动 Mock Training Service

**方式 A: 使用启动脚本（推荐）**

```bash
chmod +x scripts/start_mock_service.sh
./scripts/start_mock_service.sh
```

**方式 B: 直接运行**

```bash
python3 tests/mock_training_service.py
```

服务启动后会监听在 `http://0.0.0.0:8001`

### 2️⃣ 验证服务运行

```bash
# 健康检查
curl http://localhost:8001/health

# 查看 API 文档
open http://localhost:8001/docs  # macOS
# 或浏览器访问 http://localhost:8001/docs
```

### 3️⃣ 使用 Executor

```python
from kosmos.ai_scientist.executor import Executor
from kosmos.ai_scientist.data_structures import Configuration

# 创建 Executor（自动检测服务）
executor = Executor(
    service_url="http://localhost:8001",
    use_mock_service=True
)

# 创建配置
config = Configuration(
    recon_family="CIAS-Core-ELP",
    recon_params={"num_layers": 10, "hidden_dim": 128},
    uq_scheme="Conformal",
    uq_params={"alpha": 0.1},
    forward_config={"compression_ratio": 8},
    train_config={"epochs": 50, "lr": 0.001}
)

# 运行训练
metrics, artifacts = executor.run_campaign(config)

# 查看结果
print(f"PSNR: {metrics.psnr:.2f} dB")
print(f"Coverage: {metrics.coverage:.2%}")
```

## API 文档

### POST /train

训练接口，接收配置并返回训练结果。

**请求体 (JSON):**

```json
{
  "recon_family": "CIAS-Core-ELP",
  "recon_params": {
    "num_layers": 10,
    "hidden_dim": 128
  },
  "uq_scheme": "Conformal",
  "uq_params": {
    "alpha": 0.1
  },
  "forward_config": {
    "compression_ratio": 8
  },
  "train_config": {
    "epochs": 50,
    "lr": 0.001
  }
}
```

**响应 (JSON):**

```json
{
  "psnr": 29.45,
  "coverage": 0.9023,
  "latency": 35.2,
  "calibration_error": 0.0456,
  "checkpoint": "checkpoints/exp_a1b2c3d4/model_best.pth",
  "uq_params_fitted": {
    "threshold": 0.87,
    "alpha": 0.1,
    "quantiles": [0.05, 0.5, 0.95]
  },
  "train_log": "logs/exp_a1b2c3d4/train.log",
  "eval_samples": [
    "outputs/exp_a1b2c3d4/sample_0.png",
    "outputs/exp_a1b2c3d4/sample_1.png"
  ],
  "fig_scripts": [
    "figures/exp_a1b2c3d4/plot_metrics.py",
    "figures/exp_a1b2c3d4/plot_uncertainty.py"
  ],
  "experiment_id": "exp_a1b2c3d4",
  "duration": 0.234,
  "status": "completed"
}
```

### GET /health

健康检查接口。

**响应:**

```json
{
  "status": "healthy",
  "service": "mock_training_service",
  "timestamp": 1702985678.123
}
```

## 模拟逻辑

### PSNR 计算

- **基础值**: 根据 `recon_family`
  - CIAS-Core-ELP: 28.0 dB
  - CIAS-Core: 26.0 dB
  - Baseline-CNN: 24.0 dB

- **Epochs 影响**: 更多 epochs 通常更好（有上限）
  ```python
  epoch_boost = min(epochs / 50.0, 1.5) - 0.5
  ```

- **学习率影响**: 0.001 附近最优
  ```python
  lr_penalty = abs(lr - 0.001) * 2000
  ```

- **随机噪声**: ±1.5 dB

### Coverage 计算

- **Conformal**: 目标 coverage = 1 - alpha ± 3%
- **Ensemble**: 0.85 - 0.92
- **None**: 0.70 - 0.85

### Latency 计算

基于模型复杂度:

```python
latency = 10 + num_layers * 2 + hidden_dim / 10 + random(-5, 5)
```

## 配置

### 环境变量

```bash
# 设置服务地址（Executor 会使用）
export MOCK_TRAINING_SERVICE_URL="http://localhost:8001"

# 或在代码中指定
executor = Executor(service_url="http://custom-host:8001")
```

### Executor 模式

```python
# 模式 1: 使用服务（推荐）
executor = Executor(use_mock_service=True)

# 模式 2: 仅使用本地 mock
executor = Executor(use_mock_service=False)

# 模式 3: 自定义服务地址
executor = Executor(
    service_url="http://192.168.1.100:8001",
    use_mock_service=True
)
```

## 测试

### 运行测试脚本

```bash
python3 tests/test_executor_with_service.py
```

测试脚本会:
1. 检查服务是否运行
2. 测试使用服务模式
3. 测试本地 mock 模式
4. 显示结果对比

### 示例输出

```
🧪 Executor 测试

🔍 检查 Mock Training Service...
✅ Mock Training Service 正在运行

======================================================================
测试: Executor with Mock Training Service
======================================================================

1. 创建 Executor...
   Service available: True
   Service URL: http://localhost:8001

2. 运行实验...

   实验 1/3
   Config: CIAS-Core-ELP + Conformal
   ✅ 完成!
      PSNR: 29.12 dB
      Coverage: 89.45%
      Latency: 36.7 ms
      Calibration Error: 0.0523

...

结果汇总
最优配置:
  Recon Family: CIAS-Core-ELP
  UQ Scheme: Conformal
  PSNR: 29.12 dB
  Coverage: 89.45%
```

## 依赖

Mock Training Service 需要以下依赖:

```bash
pip install fastapi uvicorn requests
```

或使用项目的 requirements:

```bash
pip install -r requirements.txt
```

## 与 SCI Research Loop 集成

Mock Training Service 可以与整个 SCI Research Loop 集成使用:

```python
from kosmos.ai_scientist.workflow import SCIResearchWorkflow
from kosmos.ai_scientist.executor import Executor

# 启动 Mock Service (在另一个终端)
# ./scripts/start_mock_service.sh

# 创建 Workflow（会自动使用服务）
workflow = SCIResearchWorkflow(
    research_objective="优化 SCI 重建",
    design_space=design_space,
    budget_max=20
)

# Executor 会自动检测并使用 Mock Training Service
results = await workflow.run(num_cycles=3, experiments_per_cycle=3)
```

## 故障排除

### 问题 1: 服务无法启动

```
端口 8001 已被占用
```

**解决**:
```bash
# 找到占用端口的进程
lsof -i :8001

# 杀死进程或更改端口
python3 tests/mock_training_service.py --port 8002
```

### 问题 2: Executor 无法连接服务

```
Service health check failed
```

**解决**:
1. 确认服务正在运行: `curl http://localhost:8001/health`
2. 检查防火墙设置
3. 使用正确的地址: `executor = Executor(service_url="http://localhost:8001")`

### 问题 3: 依赖缺失

```
ModuleNotFoundError: No module named 'fastapi'
```

**解决**:
```bash
pip install fastapi uvicorn requests
```

## 优势

### vs 本地 Mock

| 特性 | Mock Service | 本地 Mock |
|-----|--------------|-----------|
| 结果真实性 | ⬆️ 更真实（基于配置） | ⬇️ 简单随机 |
| 可调试性 | ✅ 可独立测试 | ❌ 耦合 |
| 扩展性 | ✅ 易于扩展 | ⬇️ 修改代码 |
| 部署 | ⬇️ 需要启动服务 | ✅ 无需额外步骤 |

### 未来扩展

Mock Service 架构便于未来扩展为真实服务:

```python
# 未来: 连接真实训练集群
executor = Executor(
    service_url="http://training-cluster.example.com",
    use_mock_service=False  # 使用真实服务
)
```

## 相关文件

- **服务实现**: `tests/mock_training_service.py`
- **Executor**: `kosmos/ai_scientist/executor.py`
- **测试脚本**: `tests/test_executor_with_service.py`
- **启动脚本**: `scripts/start_mock_service.sh`

## 版本历史

- **v1.0.0** (2025-12-19): 初始版本
  - FastAPI 实现
  - 基于配置的模拟逻辑
  - Executor 集成
