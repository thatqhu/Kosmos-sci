"""
Planner Module

Implements Algorithm 3: PLANNER_STEP
LLM-based experiment designer that proposes new configurations.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging
import os

from .data_structures import WorldModel, Configuration

logger = logging.getLogger(__name__)

# Try to import LLM clients
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic package not available")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai package not available")


class Planner:
    """
    LLM-based experiment planner.

    The planner:
    - Summarizes the current world model state
    - Identifies under-explored regions of the design space
    - Generates prompts for LLM-based proposal generation
    - Validates and projects LLM proposals to valid configurations
    - Manages exploration-exploitation tradeoff
    """

    def __init__(
        self,
        anthropic_client=None,
        openai_client=None,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash-exp",
        provider: str = "auto",  # "anthropic", "openai", "auto"
        base_url: Optional[str] = None
    ):
        """
        Initialize Planner with LLM support (Anthropic or OpenAI-compatible).

        Args:
            anthropic_client: Pre-configured Anthropic client
            openai_client: Pre-configured OpenAI client
            api_key: API key (will auto-detect provider or use 'provider' arg)
            model: Model name (e.g., "gemini-2.0-flash-exp", "claude-sonnet-4-5")
            provider: "anthropic", "openai", or "auto" (auto-detect)
            base_url: Custom base URL for OpenAI-compatible APIs
        """
        self.model = model
        self.client = None
        self.provider = None

        # Priority 1: Use provided client
        if anthropic_client is not None:
            self.client = anthropic_client
            self.provider = "anthropic"
            logger.info("Planner initialized with provided Anthropic client")

        elif openai_client is not None:
            self.client = openai_client
            self.provider = "openai"
            logger.info("Planner initialized with provided OpenAI client")

        else:
            # Priority 2: Auto-detect or create from API key
            api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

            if not api_key:
                logger.warning("No API key provided for Planner, LLM features will be disabled")
                return

            # Determine provider
            if provider == "auto":
                # Auto-detect based on environment variables
                if os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY"):
                    provider = "openai"
                elif os.getenv("ANTHROPIC_API_KEY"):
                    provider = "anthropic"
                else:
                    # Default to OpenAI for Gemini
                    provider = "openai"

            # Create client based on provider
            if provider == "openai" and OPENAI_AVAILABLE:
                try:
                    # Default to Gemini endpoint if no base_url provided
                    if base_url is None:
                        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

                    self.client = OpenAI(
                        api_key=api_key,
                        base_url=base_url
                    )
                    self.provider = "openai"
                    logger.info(f"Planner initialized with OpenAI client (model={model}, base_url={base_url})")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI client: {e}")

            elif provider == "anthropic" and ANTHROPIC_AVAILABLE:
                try:
                    self.client = anthropic.Anthropic(api_key=api_key)
                    self.provider = "anthropic"
                    logger.info(f"Planner initialized with Anthropic client (model={model})")
                except Exception as e:
                    logger.warning(f"Failed to initialize Anthropic client: {e}")

            else:
                logger.warning(f"Provider '{provider}' not available or package not installed")

    @staticmethod
    def summarize_world_model(world_model: WorldModel) -> Dict[str, Any]:
        """
        Generate high-level summary of world model state.

        Extracts key statistics for planner decision-making:
        - Total experiments conducted
        - Best performance achieved
        - Distribution across configuration families
        - Current constraints

        Args:
            world_model: Current world model

        Returns:
            Summary dictionary
        """
        experiments = world_model.get_all_experiments()

        if not experiments:
            return {
                "total_experiments": 0,
                "best_psnr": 0.0,
                "frontiers": [],
                "constraints": {},
                "underexplored": ["all"]
            }

        # Extract key statistics
        best_exp = max(experiments, key=lambda e: e.metrics.psnr)
        avg_psnr = sum(e.metrics.psnr for e in experiments) / len(experiments)

        # Count configurations by type
        recon_families = defaultdict(int)
        uq_schemes = defaultdict(int)

        for exp in experiments:
            recon_families[exp.config.recon_family] += 1
            uq_schemes[exp.config.uq_scheme] += 1

        return {
            "total_experiments": len(experiments),
            "best_psnr": best_exp.metrics.psnr,
            "best_config": best_exp.config.recon_family,
            "avg_psnr": avg_psnr,
            "recon_families": dict(recon_families),
            "uq_schemes": dict(uq_schemes),
            "frontiers": [],  # Populated by analysis_step
            "constraints": {"max_latency": 100, "min_coverage": 0.8}
        }

    @staticmethod
    def identify_underexplored_regions(summary: Dict[str, Any]) -> List[str]:
        """
        Identify under-explored regions of the design space.

        Compares tested configurations against the full design space
        to find gaps in coverage.

        Args:
            summary: World model summary

        Returns:
            List of under-explored region descriptions
        """
        gaps = []

        # Check for untested reconstruction families
        all_families = ["CIAS-Core", "CIAS-Core-ELP", "Baseline-CNN"]
        tested_families = set(summary.get("recon_families", {}).keys())

        for family in all_families:
            if family not in tested_families:
                gaps.append(f"recon_family:{family}")

        # Check for untested UQ schemes
        all_uq = ["Conformal", "Ensemble", "None"]
        tested_uq = set(summary.get("uq_schemes", {}).keys())

        for uq in all_uq:
            if uq not in tested_uq:
                gaps.append(f"uq_scheme:{uq}")

        return gaps if gaps else ["explore_variations"]

    @staticmethod
    def build_planner_prompt(gaps: List[str],
                            frontiers: List[str],
                            constraints: Dict[str, Any],
                            budget: int) -> str:
        """
        Build prompt for LLM-based configuration proposal.

        Args:
            gaps: Under-explored regions
            frontiers: Current Pareto frontiers
            constraints: System constraints
            budget: Remaining experiment budget

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an AI experiment designer for snapshot compressive imaging (SCI).

Current state:
- Under-explored regions: {', '.join(gaps)}
- Pareto frontier: {len(frontiers)} configurations
- Constraints: {constraints}
- Remaining budget: {budget} experiments

Propose {min(3, budget)} new experiment configurations, prioritizing under-explored regions.
Each configuration should include: recon_family, uq_scheme, and relevant parameters.
"""
        return prompt

    def llm_generate_configs(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Generate configuration proposals using LLM.

        Supports both Anthropic and OpenAI-compatible APIs (Gemini).
        Falls back to mock proposals if LLM client is not available.

        Args:
            prompt: Formatted prompt for LLM

        Returns:
            List of proposed configuration dictionaries
        """
        if self.client is None:
            # No LLM client available, use mock proposals
            logger.info("[LLM Planner] No client available, using mock proposals")
            return self._get_mock_proposals()

        logger.info(f"[LLM Planner] Generating configurations with {self.model} (provider: {self.provider})")

        try:
            # Call LLM API based on provider
            if self.provider == "openai":
               # OpenAI-compatible API (Gemini, etc.)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=4096,
                    temperature=0.7
                )
                response_text = response.choices[0].message.content

            elif self.provider == "anthropic":
                # Anthropic API
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0.7,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                response_text = message.content[0].text
            else:
                logger.warning(f"[LLM Planner] Unknown provider: {self.provider}")
                return self._get_mock_proposals()

            logger.debug(f"[LLM Planner] Response received: {len(response_text)} chars")

            # Parse JSON response
            import json

            # Extract JSON from response (may be wrapped in markdown)
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            # Try to find JSON object
            start_idx = text.find('[')
            if start_idx == -1:
                start_idx = text.find('{')

            if start_idx != -1:
                # Find matching bracket
                if text[start_idx] == '[':
                    end_idx = text.rfind(']') + 1
                else:
                    end_idx = text.rfind('}') + 1

                json_str = text[start_idx:end_idx]
                parsed = json.loads(json_str)

                # Handle both list and dict responses
                if isinstance(parsed, list):
                    proposals = parsed
                elif isinstance(parsed, dict) and 'configurations' in parsed:
                    proposals = parsed['configurations']
                elif isinstance(parsed, dict) and 'proposals' in parsed:
                    proposals = parsed['proposals']
                else:
                    proposals = [parsed]  # Single configuration

                logger.info(f"[LLM Planner] Generated {len(proposals)} proposals")
                return proposals
            else:
                logger.warning("[LLM Planner] No JSON found in response, using mock proposals")
                return self._get_mock_proposals()

        except Exception as e:
            logger.error(f"[LLM Planner] Error calling LLM: {e}, using mock proposals")
            return self._get_mock_proposals()

    def _get_mock_proposals(self) -> List[Dict[str, Any]]:
        """
        Get mock configuration proposals (fallback when LLM unavailable).

        Returns:
            List of mock configuration dictionaries
        """
        proposals = [
            {
                "recon_family": "CIAS-Core-ELP",
                "uq_scheme": "Conformal",
                "recon_params": {"num_layers": 10, "hidden_dim": 128},
                "forward_config": {"compression_ratio": 8},
                "uq_params": {"alpha": 0.1},
                "train_config": {"epochs": 50, "lr": 0.001}
            },
            {
                "recon_family": "CIAS-Core",
                "uq_scheme": "Ensemble",
                "recon_params": {"num_layers": 8, "hidden_dim": 64},
                "forward_config": {"compression_ratio": 16},
                "uq_params": {"n_models": 5},
                "train_config": {"epochs": 40, "lr": 0.0005}
            },
            {
                "recon_family": "Baseline-CNN",
                "uq_scheme": "None",
                "recon_params": {"num_layers": 6},
                "forward_config": {"compression_ratio": 8},
                "uq_params": {},
                "train_config": {"epochs": 30, "lr": 0.001}
            }
        ]
        return proposals

    @staticmethod
    def project_to_design_space(proposal: Dict[str, Any],
                               design_space: Dict[str, List[Any]]) -> Configuration:
        """
        Project LLM proposal to valid design space configuration.

        Ensures all configuration parameters are within allowed ranges.

        Args:
            proposal: Raw LLM proposal
            design_space: Valid design space definition

        Returns:
            Valid Configuration object
        """
        # Ensure recon_family is in design space
        recon_family = proposal.get("recon_family", "CIAS-Core")
        if recon_family not in design_space.get("recon_families", []):
            recon_family = design_space["recon_families"][0]

        return Configuration(
            forward_config=proposal.get("forward_config", {}),
            recon_family=recon_family,
            recon_params=proposal.get("recon_params", {}),
            uq_scheme=proposal.get("uq_scheme", "None"),
            uq_params=proposal.get("uq_params", {}),
            train_config=proposal.get("train_config", {})
        )

    @staticmethod
    def is_valid_config(config: Configuration, constraints: Dict[str, Any]) -> bool:
        """
        Validate configuration against system constraints.

        Args:
            config: Configuration to validate
            constraints: System constraints

        Returns:
            True if valid, False otherwise
        """
        # Simple validation (extend with real constraint checking)
        return True

    def planner_step(self, summary: Dict[str, Any],
                    design_space: Dict[str, List[Any]],
                    budget_remaining: int) -> List[Configuration]:
        """
        Algorithm 3: PLANNER_STEP

        Main planner logic that:
        1. Identifies under-explored regions
        2. Builds LLM prompt
        3. Generates configuration proposals
        4. Validates and projects to design space
        5. Returns approved configurations

        Args:
            summary: World model summary
            design_space: Valid design space
            budget_remaining: Remaining experiment budget

        Returns:
            List of proposed configurations
        """
        # Identify gaps in exploration
        gaps = Planner.identify_underexplored_regions(summary)
        frontiers = summary.get("frontiers", [])
        constraints = summary.get("constraints", {})

        # Build LLM prompt
        prompt = Planner.build_planner_prompt(gaps, frontiers, constraints, budget_remaining)

        # Generate proposals via LLM (now uses instance method)
        proposals_raw = self.llm_generate_configs(prompt)

        # Validate and project to design space
        new_configs = []
        for proposal in proposals_raw:
            config = Planner.project_to_design_space(proposal, design_space)
            if Planner.is_valid_config(config, constraints):
                new_configs.append(config)

        # Truncate to budget
        if len(new_configs) > budget_remaining:
            new_configs = new_configs[:budget_remaining]

        return new_configs
