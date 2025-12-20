#!/usr/bin/env python3
"""
Mock Training Service - FastAPI 实现

模拟 SCI 重建模型的训练服务，用于测试 Executor
"""

import random
import uuid
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


# ==================== 请求/响应模型 ====================

class TrainRequest(BaseModel):
    """训练请求模型"""
    recon_family: str  # 重建算法家族（CIAS-Core, CIAS-Core-ELP, Baseline-CNN）
    recon_params: Dict[str, Any]  # 重建参数
    uq_scheme: str  # 不确定性量化方案（Conformal, Ensemble, None）
    uq_params: Dict[str, Any]  # UQ 参数
    forward_config: Dict[str, Any]  # 前向模型配置
    train_config: Dict[str, Any]  # 训练配置

    class Config:
        schema_extra = {
            "example": {
                "recon_family": "CIAS-Core-ELP",
                "recon_params": {"num_layers": 10, "hidden_dim": 128},
                "uq_scheme": "Conformal",
                "uq_params": {"alpha": 0.1},
                "forward_config": {"compression_ratio": 8},
                "train_config": {"epochs": 50, "lr": 0.001}
            }
        }


class TrainResponse(BaseModel):
    """训练响应模型"""
    # 指标
    psnr: float
    coverage: float
    latency: float
    calibration_error: Optional[float]

    # 工件
    checkpoint: str
    uq_params_fitted: Dict[str, Any]
    train_log: str
    eval_samples: list[str]
    fig_scripts: list[str]

    # 元数据
    experiment_id: str
    duration: float  # 训练耗时（秒）
    status: str


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="Mock SCI Training Service",
    description="模拟 SCI 重建模型训练服务，返回随机结果用于测试",
    version="1.0.0"
)


@app.get("/")
def root():
    """根路径"""
    return {
        "service": "Mock SCI Training Service",
        "version": "1.0.0",
        "endpoints": {
            "train": "/train",
            "health": "/health"
        }
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "mock_training_service",
        "timestamp": time.time()
    }


@app.post("/train", response_model=TrainResponse)
def train(request: TrainRequest):
    """
    训练接口 - 模拟训练过程并返回随机结果

    Args:
        request: 训练配置请求

    Returns:
        TrainResponse: 训练结果（指标 + 工件）
    """
    print(f"[Mock Service] 收到训练请求: {request.recon_family} + {request.uq_scheme}")

    # 模拟训练耗时
    start_time = time.time()
    training_time = random.uniform(0.1, 0.5)  # 模拟 0.1-0.5 秒
    time.sleep(training_time)

    # 生成实验 ID
    experiment_id = f"exp_{uuid.uuid4().hex[:12]}"

    # ========== 模拟训练结果 ==========

    # 1. 不同 recon_family 的基础性能
    base_psnr_map = {
        "CIAS-Core-ELP": 28.0,
        "CIAS-Core": 26.0,
        "Baseline-CNN": 24.0
    }
    base_psnr = base_psnr_map.get(request.recon_family, 25.0)

    # 2. 根据训练配置调整性能
    epochs = request.train_config.get("epochs", 50)
    lr = request.train_config.get("lr", 0.001)

    # 更多 epochs 通常效果更好（但有上限）
    epoch_boost = min(epochs / 50.0, 1.5) - 0.5  # -0.5 到 +1.0

    # 学习率在 0.001 附近最优
    lr_penalty = abs(lr - 0.001) * 2000  # 偏离 0.001 会降低性能

    # 3. 计算最终 PSNR
    psnr = base_psnr + epoch_boost - lr_penalty + random.uniform(-1.5, 2.0)

    # 4. Coverage 取决于 UQ scheme
    if request.uq_scheme == "Conformal":
        alpha = request.uq_params.get("alpha", 0.1)
        # Conformal 通常能达到目标 coverage (1 - alpha)
        target_coverage = 1 - alpha
        coverage = target_coverage + random.uniform(-0.03, 0.03)
    elif request.uq_scheme == "Ensemble":
        # Ensemble 通常 coverage 稍低
        coverage = random.uniform(0.85, 0.92)
    else:
        # 无 UQ 时 coverage 随机
        coverage = random.uniform(0.70, 0.85)

    # 5. Latency 取决于模型复杂度
    num_layers = request.recon_params.get("num_layers", 8)
    hidden_dim = request.recon_params.get("hidden_dim", 64)
    latency = 10 + num_layers * 2 + hidden_dim / 10 + random.uniform(-5, 5)

    # 6. Calibration Error (仅 UQ schemes)
    calibration_error = None
    if request.uq_scheme != "None":
        calibration_error = random.uniform(0.01, 0.10)

    # ========== 拟合 UQ 参数 ==========

    uq_params_fitted = {}
    if request.uq_scheme == "Conformal":
        uq_params_fitted = {
            "threshold": random.uniform(0.85, 0.95),
            "alpha": request.uq_params.get("alpha", 0.1),
            "quantiles": [0.05, 0.5, 0.95]
        }
    elif request.uq_scheme == "Ensemble":
        n_models = request.uq_params.get("n_models", 5)
        uq_params_fitted = {
            "n_models": n_models,
            "variance": random.uniform(0.03, 0.08),
            "weights": [random.random() for _ in range(n_models)]
        }

    # ========== 生成工件路径 ==========

    checkpoint = f"checkpoints/{experiment_id}/model_best.pth"
    train_log = f"logs/{experiment_id}/train.log"
    eval_samples = [
        f"outputs/{experiment_id}/sample_{i}.png"
        for i in range(random.randint(3, 5))
    ]
    fig_scripts = [
        f"figures/{experiment_id}/plot_metrics.py",
        f"figures/{experiment_id}/plot_uncertainty.py"
    ]

    # ========== 构造响应 ==========

    duration = time.time() - start_time

    response = TrainResponse(
        # 指标
        psnr=round(psnr, 2),
        coverage=round(coverage, 4),
        latency=round(max(latency, 5.0), 2),  # 至少 5ms
        calibration_error=round(calibration_error, 4) if calibration_error else None,

        # 工件
        checkpoint=checkpoint,
        uq_params_fitted=uq_params_fitted,
        train_log=train_log,
        eval_samples=eval_samples,
        fig_scripts=fig_scripts,

        # 元数据
        experiment_id=experiment_id,
        duration=round(duration, 3),
        status="completed"
    )

    print(f"[Mock Service] 训练完成: PSNR={psnr:.2f}, Coverage={coverage:.2%}, "
          f"Latency={latency:.1f}ms, ID={experiment_id}")

    return response


# ==================== 主函数 ====================

def main():
    """启动服务"""
    print("="*70)
    print("🚀 Mock SCI Training Service")
    print("="*70)
    print("正在启动服务...")
    print("API 文档: http://0.0.0.0:8001/docs")
    print("健康检查: http://0.0.0.0:8001/health")
    print("="*70)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )


if __name__ == "__main__":
    main()
