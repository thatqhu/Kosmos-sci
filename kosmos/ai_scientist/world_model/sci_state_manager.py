"""
SCI State Manager for Kosmos AI Scientist.

Extends the base ArtifactStateManager to handle SCI-specific experiment tracking.
Adds support for:
- Pareto frontier tracking
- Design space coverage analysis
- SCI experiment record storage
"""

from typing import Dict, List, Set, Optional, Any
from pathlib import Path
import logging

from kosmos.world_model.artifacts import ArtifactStateManager, Finding
from ..data_structures import ExperimentRecord, Configuration

logger = logging.getLogger(__name__)


class SCIStateManager(ArtifactStateManager):
    """
    SCI-specific state manager.

    Extends base ArtifactStateManager with:
    - Pareto frontier caching
    - Design space coverage tracking
    - SCI experiment persistence
    """

    def __init__(
        self,
        artifacts_dir: str = "artifacts/sci",
        world_model=None,
        vector_store=None
    ):
        """
        Initialize SCI State Manager.

        Args:
            artifacts_dir: Directory for SCI artifacts
            world_model: Optional knowledge graph
            vector_store: Optional vector store
        """
        super().__init__(
            artifacts_dir=artifacts_dir,
            world_model=world_model,
            vector_store=vector_store
        )

        # SCI-specific caches
        self._pareto_cache: Set[str] = set()
        self._design_space_coverage: Dict[str, List[str]] = {}

        logger.info(f"Initialized SCIStateManager at {self.artifacts_dir}")

    async def save_sci_experiment(
        self,
        cycle: int,
        experiment: ExperimentRecord
    ) -> Path:
        """
        Save SCI experiment record.

        Converts ExperimentRecord to Finding format compatible with
        the base state manager.

        Args:
            cycle: Research cycle number
            experiment: SCI experiment record

        Returns:
            Path to saved artifact
        """
        # Generate task_id based on current cycle findings
        task_id = len(self.get_all_cycle_findings(cycle))
        task_id += 1

        # Convert to Finding format
        finding = {
            "finding_id": experiment.id,
            "cycle": cycle,
            "task_id": task_id,
            "summary": (
                f"SCI配置评估: {experiment.config.recon_family} + "
                f"{experiment.config.uq_scheme}"
            ),
            "statistics": {
                "psnr": experiment.metrics.psnr,
                "coverage": experiment.metrics.coverage,
                "latency": experiment.metrics.latency,
                "calibration_error": experiment.metrics.calibration_error
            },
            "methods": (
                f"使用{experiment.config.recon_family}架构进行SCI重建，"
                f"UQ方案: {experiment.config.uq_scheme}"
            ),
            "interpretation": self._interpret_metrics(experiment.metrics),
            "evidence_type": "sci_optimization_result",
            "metadata": {
                "config": experiment.config.to_dict(),
                "artifacts": {
                    "checkpoint": experiment.artifacts.checkpoint,
                    "uq_params": experiment.artifacts.uq_params,
                    "train_log": experiment.artifacts.train_log,
                    "eval_samples": experiment.artifacts.eval_samples,
                    "fig_scripts": experiment.artifacts.fig_scripts
                },
                "pareto_optimal": experiment.id in self._pareto_cache
            }
        }

        # Update design space coverage
        family_key = experiment.config.recon_family
        if family_key not in self._design_space_coverage:
            self._design_space_coverage[family_key] = []
        self._design_space_coverage[family_key].append(experiment.id)

        # Save using base manager
        return await self.save_finding_artifact(cycle, task_id, finding)

    def _interpret_metrics(self, metrics) -> str:
        """Generate interpretation of SCI metrics."""
        interpretation = []

        if metrics.psnr > 28.0:
            interpretation.append("优秀的重建质量 (PSNR > 28dB)")
        elif metrics.psnr > 26.0:
            interpretation.append("良好的重建质量 (PSNR > 26dB)")
        else:
            interpretation.append("重建质量需要改进")

        if metrics.coverage > 0.9:
            interpretation.append("高可靠的不确定性估计 (coverage > 90%)")
        elif metrics.coverage > 0.8:
            interpretation.append("可接受的不确定性估计")

        if metrics.latency < 20.0:
            interpretation.append("快速推理 (< 20ms)")
        elif metrics.latency < 50.0:
            interpretation.append("中等推理速度")

        return "; ".join(interpretation)

    def get_pareto_frontier(self) -> Set[str]:
        """
        Get current Pareto frontier.

        Returns:
            Set of Pareto-optimal experiment IDs
        """
        return self._pareto_cache.copy()

    def update_pareto_frontier(self, pareto_ids: Set[str]):
        """
        Update Pareto frontier cache.

        Args:
            pareto_ids: New set of Pareto-optimal IDs
        """
        self._pareto_cache = pareto_ids
        logger.info(f"Updated Pareto frontier: {len(pareto_ids)} configurations")

    def get_design_space_coverage(self) -> Dict[str, int]:
        """
        Get design space coverage statistics.

        Returns:
            Dict mapping family names to experiment counts
        """
        return {
            family: len(exp_ids)
            for family, exp_ids in self._design_space_coverage.items()
        }

    def get_unexplored_families(
        self,
        all_families: List[str]
    ) -> List[str]:
        """
        Identify unexplored reconstruction families.

        Args:
            all_families: Complete list of available families

        Returns:
            List of unexplored family names
        """
        explored = set(self._design_space_coverage.keys())
        return [f for f in all_families if f not in explored]

    def get_sci_context(
        self,
        cycle: int,
        lookback: int = 3
    ) -> Dict[str, Any]:
        """
        Get SCI-specific context for planning.

        Extends base get_cycle_context with SCI-specific info.

        Args:
            cycle: Current cycle
            lookback: Number of past cycles to include

        Returns:
            Context dictionary with SCI-specific data
        """
        # Get base context
        base_context = self.get_cycle_context(cycle, lookback)

        # Add SCI-specific data
        base_context['pareto_frontier'] = list(self._pareto_cache)
        base_context['design_space_coverage'] = self.get_design_space_coverage()
        base_context['explored_configs'] = self._get_explored_configs()

        return base_context

    def _get_explored_configs(self) -> List[Dict]:
        """Extract all explored configurations."""
        all_findings = self.get_all_findings()
        configs = []

        for finding in all_findings:
            if finding.evidence_type == "sci_optimization_result":
                # Type guard: check metadata exists and is a dict
                if finding.metadata and isinstance(finding.metadata, dict):
                    if 'config' in finding.metadata:
                        configs.append(finding.metadata['config'])

        return configs
