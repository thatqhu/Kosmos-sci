"""
Analysis Agent Module

Implements Algorithm 5: ANALYSIS_STEP (CIAS-Discovery)
Computes Pareto frontiers, calibration statistics, and trend summaries.
"""

from typing import List, Set, Dict, Tuple, Any, Optional
from collections import defaultdict
import logging
import os

from .data_structures import WorldModel, ExperimentRecord

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


class AnalysisAgent:
    """
    CIAS-Discovery analysis agent.

    Responsible for:
    - Computing multi-objective Pareto frontiers
    - Calculating calibration statistics
    - Summarizing design trends in natural language
    - Identifying promising configurations
    - LLM-generated custom verification algorithms
    """

    def __init__(
        self,
        anthropic_client=None,
        openai_client=None,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash-exp",
        enable_llm_verification: bool = False,
        provider: str = "auto",
        base_url: Optional[str] = None
    ):
        """
        Initialize AnalysisAgent with LLM support (Anthropic or OpenAI-compatible).

        Args:
            anthropic_client: Pre-configured Anthropic client
            openai_client: Pre-configured OpenAI client
            api_key: API key (will auto-detect provider)
            model: Model name (e.g., "gemini-2.0-flash-exp", "claude-sonnet-4-5")
            enable_llm_verification: Enable LLM-generated verification algorithms
            provider: "anthropic", "openai", or "auto"
            base_url: Custom base URL for OpenAI-compatible APIs
        """
        self.model = model
        self.client = None
        self.enable_llm_verification = enable_llm_verification
        self.provider = None

        if not enable_llm_verification:
            logger.info("AnalysisAgent initialized with LLM verification disabled")
            return

        # Priority 1: Use provided client
        if anthropic_client is not None:
            self.client = anthropic_client
            self.provider = "anthropic"
            logger.info("AnalysisAgent initialized with provided Anthropic client")

        elif openai_client is not None:
            self.client = openai_client
            self.provider = "openai"
            logger.info("AnalysisAgent initialized with provided OpenAI client")

        else:
            # Priority 2: Auto-detect or create from API key
            api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

            if not api_key:
                logger.warning("No API key provided for AnalysisAgent, LLM verification disabled")
                return

            # Determine provider
            if provider == "auto":
                if os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY"):
                    provider = "openai"
                elif os.getenv("ANTHROPIC_API_KEY"):
                    provider = "anthropic"
                else:
                    provider = "openai"  # Default to OpenAI for Gemini

            # Create client based on provider
            if provider == "openai" and OPENAI_AVAILABLE:
                try:
                    if base_url is None:
                        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

                    self.client = OpenAI(
                        api_key=api_key,
                        base_url=base_url
                    )
                    self.provider = "openai"
                    logger.info(f"AnalysisAgent initialized with OpenAI client (model={model})")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI client: {e}")

            elif provider == "anthropic" and ANTHROPIC_AVAILABLE:
                try:
                    self.client = anthropic.Anthropic(api_key=api_key)
                    self.provider = "anthropic"
                    logger.info(f"AnalysisAgent initialized with Anthropic client (model={model})")
                except Exception as e:
                    logger.warning(f"Failed to initialize Anthropic client: {e}")
            else:
                logger.warning(f"Provider '{provider}' not available or package not installed")

    @staticmethod
    def compute_pareto_front(experiments: List[ExperimentRecord],
                            objectives: List[str] = ['psnr', 'coverage']) -> Set[str]:
        """
        Compute Pareto frontier for multi-objective optimization.

        A configuration is Pareto-optimal if no other configuration
        dominates it (i.e., is better in all objectives).

        Assumes all objectives are to be maximized.

        Args:
            experiments: List of experiment records
            objectives: List of objective metric names to optimize

        Returns:
            Set of experiment IDs on the Pareto frontier
        """
        if not experiments:
            return set()

        pareto_set = set()

        for exp1 in experiments:
            is_dominated = False
            metrics1 = exp1.metrics

            for exp2 in experiments:
                if exp1.id == exp2.id:
                    continue

                metrics2 = exp2.metrics

                # Check if exp1 is dominated by exp2
                # exp2 dominates exp1 if:
                # - exp2 is >= exp1 on all objectives, AND
                # - exp2 is strictly > exp1 on at least one objective
                dominates = True
                strictly_better_in_one = False

                for obj in objectives:
                    val1 = getattr(metrics1, obj, 0)
                    val2 = getattr(metrics2, obj, 0)

                    if val2 < val1:  # Assuming maximization
                        dominates = False
                        break
                    if val2 > val1:
                        strictly_better_in_one = True

                if dominates and strictly_better_in_one:
                    is_dominated = True
                    break

            if not is_dominated:
                pareto_set.add(exp1.id)

        return pareto_set

    @staticmethod
    def compute_calibration_stats(experiments: List[ExperimentRecord]) -> Dict[str, float]:
        """
        Compute calibration statistics for UQ schemes.

        Args:
            experiments: List of experiment records

        Returns:
            Dictionary with mean, max, and min calibration errors
        """
        calib_errors = [
            exp.metrics.calibration_error
            for exp in experiments
            if exp.metrics.calibration_error is not None
        ]

        if not calib_errors:
            return {"mean_error": 0.0, "max_error": 0.0}

        return {
            "mean_error": sum(calib_errors) / len(calib_errors),
            "max_error": max(calib_errors),
            "min_error": min(calib_errors)
        }

    @staticmethod
    def summarize_trends(experiments: List[ExperimentRecord],
                        pareto_ids: Set[str],
                        calib_stats: Dict[str, float]) -> str:
        """
        Summarize design patterns and trends in natural language.

        Args:
            experiments: List of experiment records in this stratum
            pareto_ids: Set of Pareto-optimal experiment IDs
            calib_stats: Calibration statistics

        Returns:
            Natural language summary string
        """
        pareto_exps = [e for e in experiments if e.id in pareto_ids]

        if not pareto_exps:
            return "No significant trends found."

        avg_psnr = sum(e.metrics.psnr for e in pareto_exps) / len(pareto_exps)
        best_config = max(pareto_exps, key=lambda e: e.metrics.psnr)

        summary = f"Pareto frontier contains {len(pareto_exps)} configurations. "
        summary += f"Average PSNR: {avg_psnr:.2f} dB. "
        summary += f"Best config uses {best_config.config.recon_family}, "
        summary += f"PSNR={best_config.metrics.psnr:.2f} dB. "

        if calib_stats["mean_error"] > 0:
            summary += f"Average calibration error: {calib_stats['mean_error']:.3f}."

        return summary

    @staticmethod
    def analysis_step(world_model: WorldModel) -> Tuple[Set[str], List[str]]:
        """
        Algorithm 5: ANALYSIS_STEP

        Analyzes the world model to compute Pareto frontiers and trends.
        Groups experiments by strata (e.g., recon_family × uq_scheme),
        computes Pareto frontiers and calibration stats for each stratum,
        and generates natural language summaries.

        Args:
            world_model: Current world model

        Returns:
            Tuple of (all Pareto-optimal IDs, list of trend summaries)
        """
        all_experiments = world_model.get_all_experiments()

        # Group experiments by strata (simplified: recon_family × uq_scheme)
        strata = defaultdict(list)
        for exp in all_experiments:
            key = (exp.config.recon_family, exp.config.uq_scheme)
            strata[key].append(exp)

        pareto_set_all = set()
        trends_all = []

        for stratum_key, exps_in_stratum in strata.items():
            # Compute Pareto frontier for this stratum
            pareto_ids = AnalysisAgent.compute_pareto_front(
                exps_in_stratum,
                objectives=['psnr', 'coverage']
            )
            pareto_set_all.update(pareto_ids)

            # Compute calibration statistics
            calib_stats = AnalysisAgent.compute_calibration_stats(exps_in_stratum)

            # Summarize trends
            trend_summary = AnalysisAgent.summarize_trends(
                exps_in_stratum,
                pareto_ids,
                calib_stats
            )
            trends_all.append(f"[{stratum_key}] {trend_summary}")

        return pareto_set_all, trends_all

    def generate_verification_algorithm(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate a custom verification algorithm using LLM.

        Args:
            task_description: Description of what verification is needed
            context: Context about the data structure and requirements

        Returns:
            Python code as string, or None if generation fails
        """
        if self.client is None or not self.enable_llm_verification:
            logger.warning("LLM verification not available")
            return None

        logger.info(f"[LLM Verification] Generating algorithm for: {task_description}")

        # Build prompt for code generation
        prompt = f"""You are an expert Python developer specializing in scientific computing and optimization algorithms.

Task: {task_description}

Context:
{context.get('description', 'Analyze experiment results for multi-objective optimization')}

Data Structure:
- experiments: List[ExperimentRecord]
  - Each ExperimentRecord has:
    - id: str
    - config: Configuration (with recon_family, uq_scheme, etc.)
    - metrics: Metrics (with psnr, coverage, latency, calibration_error)

Requirements:
1. Write a Python function that performs the verification task
2. Function should be named 'verify' and accept experiments as parameter
3. Return type should be clear and documented
4. Use only standard library and numpy (if needed)
5. Include error handling
6. Add docstring explaining the algorithm

Output Format:
Provide ONLY the Python code, no markdown formatting, no explanations.
Start directly with imports (if needed) and the function definition.

Example structure:
```python
def verify(experiments):
    \"\"\"
    Your verification algorithm.

    Args:
        experiments: List of ExperimentRecord objects

    Returns:
        verification_result: Description of what is returned
    \"\"\"
    # Implementation here
    pass
```

Generate the verification algorithm now:"""

        try:
            # Call Anthropic API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.2,  # Lower temperature for code generation
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = message.content[0].text.strip()

            # Extract code from response (may be wrapped in markdown)
            code = self._extract_code(response_text)

            if code:
                logger.info(f"[LLM Verification] Generated {len(code)} chars of code")
                logger.debug(f"[LLM Verification] Code:\n{code}")
                return code
            else:
                logger.warning("[LLM Verification] Failed to extract code from response")
                return None

        except Exception as e:
            logger.error(f"[LLM Verification] Error generating algorithm: {e}")
            return None

    def _extract_code(self, response_text: str) -> Optional[str]:
        """
        Extract Python code from LLM response.

        Args:
            response_text: Raw response from LLM

        Returns:
            Extracted code or None
        """
        text = response_text.strip()

        # Remove markdown code blocks if present
        if "```python" in text:
            start = text.find("```python") + 9
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()

        # If no markdown, assume entire response is code
        # Basic validation: should contain 'def '
        if "def " in text:
            return text

        return None

    def execute_verification_code(
        self,
        code: str,
        experiments: List[ExperimentRecord]
    ) -> Optional[Any]:
        """
        Execute LLM-generated verification code in a restricted environment.

        Args:
            code: Python code to execute
            experiments: List of experiment records to analyze

        Returns:
            Result from the verification function, or None if execution fails
        """
        logger.info("[LLM Verification] Executing generated code")

        try:
            # Create restricted execution environment
            # Only allow safe built-ins and specified modules
            safe_globals = {
                '__builtins__': {
                    'len': len,
                    'max': max,
                    'min': min,
                    'sum': sum,
                    'range': range,
                    'enumerate': enumerate,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'tuple': tuple,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'print': print,
                    'sorted': sorted,
                },
                'experiments': experiments,
            }

            # Execute the code
            exec(code, safe_globals)

            # Call the verify function
            if 'verify' in safe_globals:
                verify_func = safe_globals['verify']
                result = verify_func(experiments)
                logger.info(f"[LLM Verification] Execution successful, result type: {type(result)}")
                return result
            else:
                logger.error("[LLM Verification] No 'verify' function found in generated code")
                return None

        except Exception as e:
            logger.error(f"[LLM Verification] Execution error: {e}")
            return None

    def verify_pareto_with_llm(
        self,
        experiments: List[ExperimentRecord],
        objectives: List[str] = ['psnr', 'coverage']
    ) -> Tuple[Optional[Set[str]], Optional[str]]:
        """
        Compute Pareto frontier using LLM-generated verification algorithm.

        Args:
            experiments: List of experiment records
            objectives: Objectives to optimize

        Returns:
            Tuple of (pareto_set, algorithm_code) or (None, None) if failed
        """
        if not self.enable_llm_verification or self.client is None:
            logger.info("LLM verification not enabled, using standard algorithm")
            return None, None

        # Generate algorithm
        task = f"Compute Pareto frontier for multi-objective optimization with objectives: {objectives}"
        context = {
            'description': f"""
            Compute the Pareto frontier for {len(experiments)} experiments.
            Objectives to maximize: {', '.join(objectives)}

            A configuration is Pareto-optimal if no other configuration dominates it.
            Configuration A dominates B if A is >= B on ALL objectives AND strictly > on at least one.

            Return a set of experiment IDs (strings) that are on the Pareto frontier.
            """
        }

        code = self.generate_verification_algorithm(task, context)
        if code is None:
            return None, None

        # Execute the generated code
        result = self.execute_verification_code(code, experiments)

        if result is not None and isinstance(result, (set, list)):
            pareto_set = set(result) if isinstance(result, list) else result
            logger.info(f"[LLM Verification] Found {len(pareto_set)} Pareto-optimal configurations")
            return pareto_set, code
        else:
            logger.warning("[LLM Verification] Invalid result from generated code")
            return None, None
