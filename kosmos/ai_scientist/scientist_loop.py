"""
AI Scientist Loop Module

Implements Algorithm 1: CIAS-X AI Scientist Loop
Main orchestration loop for automated scientific discovery.

DEPRECATED: This module is kept for backward compatibility.
Use kosmos.ai_scientist.workflow.SCIResearchWorkflow instead.
"""

from typing import Dict, List, Any, Set, Tuple
from .data_structures import WorldModel, Configuration

# Import from new location - use local WorldModelManager for compatibility
class WorldModelManager:
    """Deprecated compatibility wrapper."""
    @staticmethod
    def update(world_model, config, metrics, artifacts):
        from .data_structures import ExperimentRecord
        import uuid
        experiment = ExperimentRecord(
            id=str(uuid.uuid4()),
            config=config,
            metrics=metrics,
            artifacts=artifacts
        )
        world_model.experiments.append(experiment)
        return world_model

from .executor import Executor
from .analysis import AnalysisAgent
from .planner import Planner



class AIScientistLoop:
    """
    CIAS-X AI Scientist main loop.

    Orchestrates the complete automated discovery process:
    1. Initializes world model with seed experiments
    2. Iteratively:
       a. Summarizes current knowledge
       b. Plans new experiments (LLM-based), this part will research uncovered config
       c. Executes experiments
       d. Analyzes results (Pareto, trends)
       e. Updates planner context
    3. Returns final Pareto set and world model
    """

    def __init__(self,
                 design_space: Dict[str, List[Any]],
                 initial_configs: List[Configuration],
                 budget_max: int):
        """
        Initialize AI Scientist Loop.

        Args:
            design_space: Design space definition (families, schemes, etc.)
            initial_configs: Seed configurations (human baselines)
            budget_max: Maximum experiment budget
        """
        self.design_space = design_space
        self.initial_configs = initial_configs
        self.budget_max = budget_max
        self.world_model = WorldModel()
        self.planner_context: dict[str, Any] = {}

    def run(self) -> Tuple[Set[str], WorldModel]:
        """
        Algorithm 1: CIAS-X AI Scientist Loop

        Main execution loop:
        - Phase 1: Initialize with seed experiments
        - Phase 2: Iterative discovery loop (plan → execute → analyze)
        - Phase 3: Return final Pareto set and world model

        Returns:
            Tuple of (Pareto set IDs, final world model)
        """
        print("=" * 60)
        print("CIAS-X AI Scientist Loop Started")
        print("=" * 60)

        # Phase 1: Initialize world model with seed experiments
        print("\nPhase 1: Initializing world model")
        for i, config in enumerate(self.initial_configs, 1):
            print(f"\nInitial experiment {i}/{len(self.initial_configs)}")
            metrics, artifacts = Executor.run_campaign(config)
            self.world_model = WorldModelManager.update(
                self.world_model, config, metrics, artifacts
            )

        budget_used = len(self.initial_configs)
        iteration = 0

        # Phase 2: Main discovery loop
        while budget_used < self.budget_max:
            iteration += 1
            print("\n" + "=" * 60)
            print(f"Iteration {iteration} (Budget used: {budget_used}/{self.budget_max})")
            print("=" * 60)

            # (A) Summarize current world model
            print("\nPhase A: Summarizing world model")
            summary = Planner.summarize_world_model(self.world_model)
            print(f"  Total experiments: {summary['total_experiments']}")
            print(f"  Best PSNR: {summary['best_psnr']:.2f} dB")
            print(f"  Average PSNR: {summary['avg_psnr']:.2f} dB")

            # (B) Planner proposes new configurations
            print("\nPhase B: Planner proposing new configurations")
            budget_remaining = self.budget_max - budget_used
            new_configs = Planner.planner_step(
                summary,
                self.design_space,
                budget_remaining
            )
            print(f"  Proposed {len(new_configs)} new configurations")

            # (C) Executor runs campaigns
            print("\nPhase C: Executing new configurations")
            for j, config in enumerate(new_configs, 1):
                print(f"\n  New experiment {j}/{len(new_configs)}")
                metrics, artifacts = Executor.run_campaign(config)
                self.world_model = WorldModelManager.update(
                    self.world_model, config, metrics, artifacts
                )
                budget_used += 1

                if budget_used >= self.budget_max:
                    print(f"\n  Budget limit reached ({self.budget_max})")
                    break

            # (D) Analysis updates frontiers and trends
            print("\nPhase D: Analyzing results")
            pareto_set, trends = AnalysisAgent.analysis_step(self.world_model)
            print(f"  Pareto frontier size: {len(pareto_set)}")
            for trend in trends:
                print(f"  {trend}")

            # (E) Update planner context with trends
            self.planner_context['trends'] = trends
            self.planner_context['pareto_size'] = len(pareto_set)

        # Phase 3: Final analysis
        print(f"\n{'=' * 60}")
        print("AI Scientist Loop Completed!")
        print(f"{'=' * 60}")
        print(f"Total experiments conducted: {len(self.world_model.experiments)}")

        final_pareto, final_trends = AnalysisAgent.analysis_step(self.world_model)

        return final_pareto, self.world_model
