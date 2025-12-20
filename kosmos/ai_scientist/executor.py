"""
Executor Module

Implements Algorithm 4: EXECUTOR_RUN_CAMPAIGN
Executes experiment configurations and returns results.

Version: 2.0.0
Updated: 2025-12-19

Changelog:
    v2.0.0 (2025-12-19):
        - 添加 Mock Training Service 调用支持
        - 支持通过环境变量配置服务地址
        - 保留本地 mock 作为后备方案

    v1.0.0:
        - 初始版本（本地 mock）
"""

import uuid
import random
import os
from typing import Tuple, Dict, Any, Optional
import logging

from .data_structures import Configuration, Metrics, Artifacts

logger = logging.getLogger(__name__)


class Executor:
    """
    Experiment executor for CIAS-Lab campaigns.

    The executor:
    - Instantiates forward models and reconstruction networks
    - Trains models with specified configurations
    - Calibrates uncertainty quantification schemes
    - Evaluates on test sets
    - Saves artifacts (checkpoints, logs, samples)

    Supports two modes:
    1. Mock Training Service (HTTP API) - 推荐用于测试
    2. Local Mock (fallback) - 当服务不可用时
    """

    def __init__(self, service_url: Optional[str] = None, use_mock_service: bool = True):
        """
        Initialize Executor.

        Args:
            service_url: Mock training service URL (e.g., "http://localhost:8001")
                        If None, will use MOCK_TRAINING_SERVICE_URL env var
            use_mock_service: If True, try to use mock service; if False, use local mock
        """
        self.use_mock_service = use_mock_service
        self.service_url = service_url or os.getenv("MOCK_TRAINING_SERVICE_URL", "http://localhost:8001")

        # 检查服务是否可用
        self.service_available = False
        if self.use_mock_service:
            self.service_available = self._check_service_health()

        if self.service_available:
            logger.info(f"✓ Mock Training Service 可用: {self.service_url}")
        else:
            logger.warning(f"⚠️  Mock Training Service 不可用，将使用本地 mock")

    def _check_service_health(self) -> bool:
        """检查 Mock Training Service 是否可用"""
        try:
            import requests
            response = requests.get(f"{self.service_url}/health", timeout=2)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Service health check failed: {e}")
            return False

    def run_campaign(self, config: Configuration) -> Tuple[Metrics, Artifacts]:
        """
        Algorithm 4: EXECUTOR_RUN_CAMPAIGN

        Executes a complete experiment campaign for the given configuration.

        实现方式:
        1. 优先调用 Mock Training Service (如果可用)
        2. 否则使用本地 mock implementation

        Args:
            config: Experiment configuration

        Returns:
            Tuple of (metrics, artifacts)
        """
        print(f"  Executing config: {config.recon_family} / {config.uq_scheme}")

        # 尝试使用 Mock Training Service
        if self.service_available:
            try:
                return self._run_via_service(config)
            except Exception as e:
                logger.warning(f"Service call failed: {e}, falling back to local mock")
                self.service_available = False  # 标记服务不可用

        # Fallback: 使用本地 mock
        return self._run_local_mock(config)

    def _run_via_service(self, config: Configuration) -> Tuple[Metrics, Artifacts]:
        """通过 Mock Training Service 执行训练"""
        import requests

        # 构造请求
        request_data = {
            "recon_family": config.recon_family,
            "recon_params": config.recon_params,
            "uq_scheme": config.uq_scheme,
            "uq_params": config.uq_params,
            "forward_config": config.forward_config,
            "train_config": config.train_config
        }

        logger.debug(f"Calling Mock Training Service: {self.service_url}/train")

        # 调用服务
        response = requests.post(
            f"{self.service_url}/train",
            json=request_data,
            timeout=30
        )
        response.raise_for_status()

        # 解析响应
        result = response.json()

        logger.info(
            f"✓ Training completed via service: "
            f"PSNR={result['psnr']:.2f}, "
            f"Duration={result['duration']:.2f}s"
        )

        # 构造 Metrics
        metrics = Metrics(
            psnr=result['psnr'],
            coverage=result['coverage'],
            latency=result['latency'],
            calibration_error=result.get('calibration_error')
        )

        # 构造 Artifacts
        artifacts = Artifacts(
            checkpoint=result['checkpoint'],
            uq_params=result['uq_params_fitted'],
            train_log=result['train_log'],
            eval_samples=result['eval_samples'],
            fig_scripts=result['fig_scripts']
        )

        return metrics, artifacts

    def _run_local_mock(self, config: Configuration) -> Tuple[Metrics, Artifacts]:
        """
        本地 Mock 实现（后备方案）

        当 Mock Training Service 不可用时使用
        """
        # Step 4: Calibrate UQ scheme
        uq_params_fitted = {}
        if config.uq_scheme == "Conformal":
            uq_params_fitted = {"threshold": 0.9, "alpha": 0.1}
        elif config.uq_scheme == "Ensemble":
            uq_params_fitted = {"n_models": 5, "variance": 0.05}

        # Step 5: Evaluate on test set (SIMULATED)
        base_psnr = 28.0 if config.recon_family == "CIAS-Core-ELP" else 26.0
        metrics = Metrics(
            psnr=base_psnr + random.uniform(-2, 3),
            coverage=random.uniform(0.85, 0.95),
            latency=random.uniform(10, 50),
            calibration_error=random.uniform(0.01, 0.1) if config.uq_scheme != "None" else None
        )

        # Step 6: Save artifacts
        artifacts = Artifacts(
            checkpoint=f"checkpoint_{uuid.uuid4().hex[:8]}.pth",
            uq_params=uq_params_fitted,
            train_log=f"train_log_{uuid.uuid4().hex[:8]}.txt",
            eval_samples=[f"sample_{i}.png" for i in range(3)],
            fig_scripts=[f"figure_{i}.py" for i in range(2)]
        )

        return metrics, artifacts
