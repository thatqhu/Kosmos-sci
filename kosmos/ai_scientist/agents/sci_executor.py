"""
SCI Executor Agent for Kosmos AI Scientist.

Wraps the original Executor to make it compatible with the ResearchWorkflow.
"""

from typing import Dict, Any
import logging

from kosmos.agents.base import BaseAgent
from ..data_structures import Configuration
from ..executor import Executor

logger = logging.getLogger(__name__)


class SCIExecutorAgent(BaseAgent):
    """
    SCI Experiment Executor Agent.

    Executes SCI reconstruction experiments and returns findings
    in the standard workflow format.
    """

    def __init__(self):
        """Initialize SCI Executor Agent."""
        self.executor = Executor()
        self.name = "SCIExecutorAgent"

    async def execute(
        self,
        task: Dict,
        cycle: int,
        context: Dict
    ) -> Dict[str, Any]:
        """
        Execute SCI experiment task.

        Args:
            task: Task dictionary with 'metadata.sci_config'
            cycle: Current cycle number
            context: Execution context

        Returns:
            Finding dictionary with experiment results
        """
        logger.info(f"Executing SCI experiment: {task.get('description', 'N/A')}")

        # Extract configuration from task metadata
        sci_config_dict = task.get('metadata', {}).get('sci_config', {})

        if not sci_config_dict:
            raise ValueError("Task metadata missing 'sci_config'")

        # Build Configuration object
        config = Configuration(
            forward_config=sci_config_dict.get('forward_config', {}),
            recon_family=sci_config_dict.get('recon_family', 'CIAS-Core'),
            recon_params=sci_config_dict.get('recon_params', {}),
            uq_scheme=sci_config_dict.get('uq_scheme', 'None'),
            uq_params=sci_config_dict.get('uq_params', {}),
            train_config=sci_config_dict.get('train_config', {})
        )

        logger.debug(f"  Config: {config.recon_family} + {config.uq_scheme}")

        # Execute experiment using original Executor
        try:
            metrics, artifacts = self.executor.run_campaign(config)
        except Exception as e:
            logger.error(f"Experiment execution failed: {e}")
            raise

        # Generate unique finding ID
        import uuid
        finding_id = f"sci_exp_{uuid.uuid4().hex[:8]}"

        # Convert to workflow-standard finding format
        finding = {
            "finding_id": finding_id,  # Add unique ID
            "summary": (
                f"SCI实验: {config.recon_family} + {config.uq_scheme} "
                f"性能评估"
            ),
            "statistics": {
                "psnr": metrics.psnr,
                "coverage": metrics.coverage,
                "latency": metrics.latency,
                "calibration_error": metrics.calibration_error
            },
            "methods": self._describe_methods(config),
            "interpretation": self._interpret_results(metrics, config),
            "evidence_type": "sci_experiment",
            "notebook_path": artifacts.train_log,
            "metadata": {
                "config": config.to_dict(),
                "artifacts": {
                    "checkpoint": artifacts.checkpoint,
                    "uq_params": artifacts.uq_params,
                    "train_log": artifacts.train_log,
                    "eval_samples": artifacts.eval_samples,
                    "fig_scripts": artifacts.fig_scripts
                }
            }
        }

        logger.info(
            f"  Results: PSNR={metrics.psnr:.2f}dB, "
            f"Coverage={metrics.coverage:.2%}, "
            f"Latency={metrics.latency:.1f}ms"
        )

        return finding

    def _describe_methods(self, config: Configuration) -> str:
        """Generate methods description."""
        method_desc = [
            f"使用{config.recon_family}架构进行Snapshot Compressive Imaging重建训练。"
        ]

        if config.recon_params:
            params_str = ", ".join(
                f"{k}={v}" for k, v in config.recon_params.items()
            )
            method_desc.append(f"网络参数: {params_str}。")

        if config.uq_scheme != "None":
            method_desc.append(
                f"应用{config.uq_scheme}不确定性量化方案进行置信度估计。"
            )

        if config.train_config:
            epochs = config.train_config.get('epochs', 'N/A')
            lr = config.train_config.get('lr', 'N/A')
            method_desc.append(f"训练配置: epochs={epochs}, learning_rate={lr}。")

        return " ".join(method_desc)

    def _interpret_results(self, metrics, config: Configuration) -> str:
        """Generate interpretation of results."""
        interpretation = []

        # PSNR interpretation
        if metrics.psnr > 28.0:
            interpretation.append(
                f"配置 {config.recon_family} + {config.uq_scheme} "
                "达到优秀的重建质量 (PSNR > 28dB)"
            )
        elif metrics.psnr > 26.0:
            interpretation.append(
                f"配置 {config.recon_family} + {config.uq_scheme} "
                "达到良好的重建质量 (PSNR > 26dB)"
            )
        else:
            interpretation.append(
                f"配置 {config.recon_family} + {config.uq_scheme} "
                "的重建质量有待提升"
            )

        # Coverage interpretation
        if config.uq_scheme != "None":
            if metrics.coverage > 0.9:
                interpretation.append(
                    "不确定性估计高度可靠 (coverage > 90%)"
                )
            elif metrics.coverage > 0.8:
                interpretation.append(
                    "不确定性估计可接受 (coverage > 80%)"
                )
            else:
                interpretation.append(
                    "不确定性估计需要校准"
                )

        # Latency interpretation
        if metrics.latency < 20.0:
            interpretation.append("推理速度非常快 (< 20ms)")
        elif metrics.latency < 50.0:
            interpretation.append("推理速度适中 (< 50ms)")
        else:
            interpretation.append("推理速度较慢，需要优化")

        return "。".join(interpretation) + "。"
