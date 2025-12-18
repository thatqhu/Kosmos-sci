"""
SCI Research Workflow for Kosmos AI Scientist.

Implements a specialized research workflow for SCI reconstruction optimization,
compatible with the main ResearchWorkflow architecture.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from ..world_model.sci_state_manager import SCIStateManager
from ..agents.sci_executor import SCIExecutorAgent
from ..data_structures import ExperimentRecord, Configuration
from ..analysis import AnalysisAgent

logger = logging.getLogger(__name__)


class SCIResearchWorkflow:
    """
    SCI Optimization Research Workflow.

    Specialized workflow for multi-objective optimization of SCI reconstruction,
    following the ResearchWorkflow design pattern but adapted for the specific
    needs of SCI experiments.

    Key differences from general workflow:
    - Focus on configuration optimization vs general research
    - Pareto frontier analysis instead of hypothesis testing
    - Design space exploration instead of literature search
    """

    def __init__(
        self,
        research_objective: str,
        design_space: Dict[str, List[Any]],
        initial_configs: Optional[List[Configuration]] = None,
        optimization_objectives: List[str] = ['psnr', 'coverage'],
        anthropic_client=None,
        artifacts_dir: str = "artifacts/sci",
        budget_max: int = 50,
        enable_llm_verification: bool = False
    ):
        """
        Initialize SCI Research Workflow.

        Args:
            research_objective: Description of optimization goal
            design_space: Dict defining valid configuration space
            initial_configs: Seed configurations (optional)
            optimization_objectives: Metrics to optimize
            anthropic_client: Anthropic client for LLM-based planning
            artifacts_dir: Directory for artifacts
            budget_max: Maximum number of experiments
            enable_llm_verification: Enable LLM-generated verification algorithms
        """
        self.research_objective = research_objective
        self.design_space = design_space
        self.initial_configs = initial_configs or []
        self.optimization_objectives = optimization_objectives
        self.budget_max = budget_max
        self.experiments_conducted = 0
        self.anthropic_client = anthropic_client

        logger.info("Initializing SCI Research Workflow...")

        # Initialize state management
        self.state_manager = SCIStateManager(artifacts_dir=artifacts_dir)
        logger.info("✓ SCI State Manager initialized")

        # Initialize executor
        self.executor = SCIExecutorAgent()
        logger.info("✓ SCI Executor initialized")

        # Initialize Planner with LLM support
        from ..planner import Planner
        self.planner = Planner(anthropic_client=anthropic_client)
        logger.info("✓ SCI Planner initialized")

        # Initialize AnalysisAgent with optional LLM verification
        from ..analysis import AnalysisAgent
        self.analysis_agent = AnalysisAgent(
            anthropic_client=anthropic_client,
            enable_llm_verification=enable_llm_verification
        )
        logger.info(f"✓ SCI Analysis Agent initialized (LLM verification: {enable_llm_verification})")

        # Tracking
        self.cycle_results = []
        self.pareto_history = []
        self.start_time = None

    async def run(
        self,
        num_cycles: int = 10,
        experiments_per_cycle: int = 5
    ) -> Dict[str, Any]:
        """
        Run SCI optimization workflow.

        Args:
            num_cycles: Number of optimization cycles
            experiments_per_cycle: Experiments to run per cycle

        Returns:
            Dict with optimization results:
            - total_experiments: Number of experiments run
            - cycles_completed: Number of cycles completed
            - final_pareto_size: Size of final Pareto frontier
            - best_configuration: Best performing configuration
            - best_metrics: Metrics of best configuration
        """
        self.start_time = datetime.now()

        logger.info(
            f"\n{'='*70}\n"
            f"Starting SCI Research Workflow\n"
            f"Objective: {self.research_objective}\n"
            f"Design Space: {len(self.design_space.get('recon_families', []))} "
            f"families, {len(self.design_space.get('uq_schemes', []))} UQ schemes\n"
            f"Cycles: {num_cycles}\n"
            f"Budget: {self.budget_max} experiments\n"
            f"{'='*70}\n"
        )

        # Phase 1: Seed experiments if provided
        if self.initial_configs:
            await self._run_seed_experiments()

        # Phase 2: Optimization cycles
        for cycle in range(1, num_cycles + 1):
            logger.info(f"\n--- Cycle {cycle}/{num_cycles} ---")

            try:
                cycle_result = await self._execute_cycle(cycle, experiments_per_cycle)
                self.cycle_results.append(cycle_result)

                logger.info(
                    f"Cycle {cycle} complete: "
                    f"{cycle_result['experiments_run']} experiments, "
                    f"Pareto frontier: {cycle_result['pareto_size']}"
                )

                # Budget check
                if self.experiments_conducted >= self.budget_max:
                    logger.info(f"Budget limit reached: {self.budget_max}")
                    break

            except Exception as e:
                logger.error(f"Cycle {cycle} failed: {e}", exc_info=True)
                continue

        # Phase 3: Final analysis
        return await self._finalize_results()

    async def _run_seed_experiments(self):
        """Run initial seed experiments."""
        logger.info(f"\nRunning {len(self.initial_configs)} seed experiments...")

        for i, config in enumerate(self.initial_configs, 1):
            logger.info(f"  Seed {i}/{len(self.initial_configs)}")

            # Create task for executor
            task = {
                'description': f"Seed experiment: {config.recon_family}",
                'metadata': {'sci_config': config.to_dict()}
            }

            # Execute
            finding = await self.executor.execute(task, cycle=0, context={})

            # Generate finding_id if not present
            if 'finding_id' not in finding:
                finding['finding_id'] = f"seed_{i}"

            # Create experiment record
            experiment = ExperimentRecord(
                id=finding['finding_id'],
                config=config,
                metrics=self._extract_metrics(finding),
                artifacts=self._extract_artifacts(finding)
            )

            # Save
            await self.state_manager.save_sci_experiment(cycle=0, experiment=experiment)
            self.experiments_conducted += 1

    async def _execute_cycle(
        self,
        cycle: int,
        num_experiments: int
    ) -> Dict[str, Any]:
        """
        Execute single optimization cycle.

        Args:
            cycle: Cycle number
            num_experiments: Number of experiments to run

        Returns:
            Cycle result dictionary
        """
        # Step 1: Get context
        context = self.state_manager.get_sci_context(cycle, lookback=3)

        logger.info(
            f"  Context: {len(context.get('explored_configs', []))} "
            f"explored configs"
        )

        # Step 2: Generate experiment plan
        # TODO: Use real plan creator when implemented
        proposed_configs = self._simple_planning(context, num_experiments)

        logger.info(f"  Proposed {len(proposed_configs)} new experiments")

        # Step 3: Execute experiments
        cycle_experiments = []
        for i, config in enumerate(proposed_configs, 1):
            if self.experiments_conducted >= self.budget_max:
                break

            logger.info(f"  Experiment {i}/{len(proposed_configs)}")

            # Create task
            task = {
                'task_id': i,
                'description': f"{config.recon_family} + {config.uq_scheme}",
                'metadata': {'sci_config': config.to_dict()}
            }

            # Execute
            finding = await self.executor.execute(task, cycle, context)

            # Create experiment record
            experiment = ExperimentRecord(
                id=finding['finding_id'],
                config=config,
                metrics=self._extract_metrics(finding),
                artifacts=self._extract_artifacts(finding)
            )

            # Save
            await self.state_manager.save_sci_experiment(cycle, experiment)
            cycle_experiments.append(experiment)
            self.experiments_conducted += 1

        logger.info(f"  Executed {len(cycle_experiments)} experiments")

        # Step 4: Pareto analysis
        pareto_ids, trends = self._analyze_pareto(cycle_experiments)

        self.state_manager.update_pareto_frontier(pareto_ids)
        self.pareto_history.append({
            'cycle': cycle,
            'pareto_size': len(pareto_ids),
            'experiments_run': len(cycle_experiments)
        })

        logger.info(f"  Pareto frontier: {len(pareto_ids)} configurations")
        for trend in trends:
            logger.info(f"    {trend}")

        # Step 5: Generate cycle summary
        await self.state_manager.generate_cycle_summary(cycle)

        return {
            'cycle': cycle,
            'experiments_run': len(cycle_experiments),
            'pareto_size': len(pareto_ids),
            'trends': trends
        }

    def _simple_planning(
        self,
        context: Dict,
        num_experiments: int
    ) -> List[Configuration]:
        """
        Experiment planning using Planner with LLM support.

        Explores unexplored families and UQ combinations using the Planner agent.
        """
        # Get explored configs
        explored_configs = context.get('explored_configs', [])

        # Create summary for planner
        summary = {
            'total_experiments': len(explored_configs),
            'recon_families': {},
            'uq_schemes': {}
        }

        for config in explored_configs:
            family = config.get('recon_family', '')
            uq = config.get('uq_scheme', '')
            summary['recon_families'][family] = summary['recon_families'].get(family, 0) + 1
            summary['uq_schemes'][uq] = summary['uq_schemes'].get(uq, 0) + 1

        # Add optimization-specific info
        summary['frontiers'] = []  # Can add Pareto frontier info
        summary['constraints'] = {
            'max_latency': 100,
            'min_coverage': 0.8
        }

        # Use Planner instance (now with LLM support)
        budget = min(num_experiments, self.budget_max - self.experiments_conducted)
        configs = self.planner.planner_step(summary, self.design_space, budget)

        logger.info(f"Planner proposed {len(configs)} configurations")

        return configs

    def _analyze_pareto(
        self,
        experiments: List[ExperimentRecord]
    ):
        """
        Analyze Pareto frontier using AnalysisAgent.

        Optionally uses LLM-generated verification if enabled.
        """
        from ..data_structures import WorldModel

        # Build world model
        world_model = WorldModel()
        world_model.experiments = experiments

        # Run analysis using AnalysisAgent instance
        pareto_ids, trends = self.analysis_agent.analysis_step(world_model)

        logger.info(f"Analysis found {len(pareto_ids)} Pareto-optimal configurations")

        return pareto_ids, trends

    def _extract_metrics(self, finding: Dict):
        """Extract metrics from finding."""
        from ..data_structures import Metrics

        stats = finding['statistics']
        return Metrics(
            psnr=stats['psnr'],
            coverage=stats['coverage'],
            latency=stats['latency'],
            calibration_error=stats.get('calibration_error')
        )

    def _extract_artifacts(self, finding: Dict):
        """Extract artifacts from finding."""
        from ..data_structures import Artifacts

        art = finding['metadata']['artifacts']
        return Artifacts(
            checkpoint=art['checkpoint'],
            uq_params=art['uq_params'],
            train_log=art['train_log'],
            eval_samples=art['eval_samples'],
            fig_scripts=art['fig_scripts']
        )

    async def _finalize_results(self) -> Dict[str, Any]:
        """Generate final results."""
        total_time = (datetime.now() - self.start_time).total_seconds()

        # Get all findings
        all_findings = self.state_manager.get_all_findings()
        sci_findings = [
            f for f in all_findings
            if f.evidence_type == "sci_optimization_result"
        ]

        # Get Pareto frontier
        pareto_ids = self.state_manager.get_pareto_frontier()
        pareto_findings = [f for f in sci_findings if f.finding_id in pareto_ids]

        # Find best configuration
        if pareto_findings:
            best_finding = max(
                pareto_findings,
                key=lambda f: f.statistics.get('psnr', 0)
            )
            best_config = best_finding.metadata['config']
            best_metrics = best_finding.statistics
        else:
            best_config = None
            best_metrics = None

        results = {
            'total_experiments': self.experiments_conducted,
            'cycles_completed': len(self.cycle_results),
            'final_pareto_size': len(pareto_ids),
            'best_configuration': best_config,
            'best_metrics': best_metrics,
            'pareto_history': self.pareto_history,
            'total_time': total_time
        }

        logger.info(
            f"\n{'='*70}\n"
            f"SCI Research Workflow Complete!\n"
            f"Experiments: {results['total_experiments']}\n"
            f"Cycles: {results['cycles_completed']}\n"
            f"Pareto Frontier: {results['final_pareto_size']} configurations\n"
            f"Best PSNR: {best_metrics['psnr'] if best_metrics else 'N/A':.2f}dB\n"
            f"Time: {total_time:.1f}s\n"
            f"{'='*70}\n"
        )

        return results

    # ============================================================================
    # Kosmos Integration Interface (for future integration)
    # ============================================================================

    def get_cycle_context(self, cycle: int, lookback: int = 3) -> Dict[str, Any]:
        """
        Get context for a cycle (Kosmos-compatible interface).

        This method provides a unified interface compatible with Kosmos'
        ResearchWorkflow.get_cycle_context() format.

        Args:
            cycle: Current cycle number
            lookback: Number of past cycles to include

        Returns:
            Context dictionary with explored configs and findings
        """
        return self.state_manager.get_sci_context(cycle, lookback)

    def to_research_finding(self, experiment: ExperimentRecord) -> Dict[str, Any]:
        """
        Convert SCI experiment to Kosmos Finding format.

        Args:
            experiment: SCI experiment record

        Returns:
            Dictionary in Kosmos Finding format
        """
        return {
            'finding_id': experiment.id,
            'summary': (
                f"SCI Config: {experiment.config.recon_family} + "
                f"{experiment.config.uq_scheme} - "
                f"PSNR: {experiment.metrics.psnr:.2f}dB, "
                f"Coverage: {experiment.metrics.coverage:.2%}"
            ),
            'statistics': {
                'psnr': experiment.metrics.psnr,
                'coverage': experiment.metrics.coverage,
                'latency': experiment.metrics.latency,
                'calibration_error': experiment.metrics.calibration_error
            },
            'evidence_type': 'sci_optimization_result',
            'metadata': {
                'config': experiment.config.to_dict(),
                'artifacts': experiment.artifacts.to_dict()
            }
        }

    def get_all_findings_as_research_format(self) -> List[Dict[str, Any]]:
        """
        Get all SCI experiments in Kosmos Finding format.

        Returns:
            List of findings compatible with Kosmos ResearchWorkflow
        """
        all_findings = self.state_manager.get_all_findings()
        return [
            self.to_research_finding(exp)
            for exp in all_findings
            if hasattr(exp, 'config') and hasattr(exp, 'metrics')
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics (Kosmos-compatible interface).

        Returns:
            Dictionary with workflow statistics
        """
        return {
            'workflow': {
                'type': 'sci_optimization',
                'research_objective': self.research_objective,
                'optimization_objectives': self.optimization_objectives,
                'budget_max': self.budget_max,
                'experiments_conducted': self.experiments_conducted,
                'cycles_completed': len(self.cycle_results)
            },
            'state_manager': {
                'total_experiments': len(self.state_manager.get_all_findings()),
                'pareto_frontier_size': len(self.state_manager.get_pareto_frontier())
            },
            'planner': {
                'type': 'sci_planner',
                'llm_enabled': self.planner.client is not None
            },
            'analysis': {
                'type': 'sci_analysis',
                'llm_verification_enabled': self.analysis_agent.enable_llm_verification
            }
        }

    async def generate_report(self) -> str:
        """
        Generate research report (Kosmos-compatible interface).

        Returns:
            Markdown-formatted report
        """
        results = await self._finalize_results() if not self.cycle_results else self.cycle_results[-1]

        report = f"# SCI Optimization Report\n\n"
        report += f"**Objective**: {self.research_objective}\n"
        report += f"**Date**: {datetime.now().strftime('%Y-%m-%d')}\n"
        report += f"**Experiments Conducted**: {self.experiments_conducted}\n\n"

        report += f"## Summary\n\n"
        report += f"This SCI optimization workflow completed {len(self.cycle_results)} cycles, "
        report += f"conducting {self.experiments_conducted} experiments.\n\n"

        # Pareto frontier
        pareto_ids = self.state_manager.get_pareto_frontier()
        report += f"## Pareto Frontier ({len(pareto_ids)} configurations)\n\n"

        all_findings = self.state_manager.get_all_findings()
        pareto_findings = [f for f in all_findings if f.finding_id in pareto_ids]

        for i, finding in enumerate(pareto_findings[:10], 1):
            report += f"### Configuration {i}\n\n"
            stats = finding.statistics
            report += f"- **PSNR**: {stats.get('psnr', 0):.2f} dB\n"
            report += f"- **Coverage**: {stats.get('coverage', 0):.2%}\n"
            report += f"- **Latency**: {stats.get('latency', 0):.1f} ms\n\n"

        return report
