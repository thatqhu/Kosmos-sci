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
        budget_max: int = 50
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
        """
        self.research_objective = research_objective
        self.design_space = design_space
        self.initial_configs = initial_configs or []
        self.optimization_objectives = optimization_objectives
        self.budget_max = budget_max
        self.experiments_conducted = 0

        logger.info("Initializing SCI Research Workflow...")

        # Initialize components
        self.state_manager = SCIStateManager(artifacts_dir=artifacts_dir)
        logger.info("✓ SCI State Manager initialized")

        self.executor = SCIExecutorAgent()
        logger.info("✓ SCI Executor initialized")

        # TODO: Replace with real SCIPlanCreatorAgent when implemented
        self.plan_creator = None  # Will use simple planning for now

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
        Simple experiment planning (placeholder for real planner).

        Explores unexplored families and UQ combinations.
        """
        from ..planner import Planner

        # Get explored configs
        explored_configs = context.get('explored_configs', [])

        # Create summary
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

        # Use original planner
        budget = min(num_experiments, self.budget_max - self.experiments_conducted)
        configs = Planner.planner_step(summary, self.design_space, budget)

        return configs

    def _analyze_pareto(
        self,
        experiments: List[ExperimentRecord]
    ):
        """Analyze Pareto frontier."""
        from ..data_structures import WorldModel

        # Build world model
        world_model = WorldModel()
        world_model.experiments = experiments

        # Run analysis
        pareto_ids, trends = AnalysisAgent.analysis_step(world_model)

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
