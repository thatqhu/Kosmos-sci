"""
CIAS-X AI Scientist Loop Framework
A modular implementation of automated scientific discovery for SCI.

Refactored to use ResearchWorkflow architecture.
"""

# Core data structures (preserved)
from .data_structures import Configuration, Metrics, Artifacts, ExperimentRecord, WorldModel

# New workflow architecture
from .workflow import SCIResearchWorkflow
from .world_model import SCIStateManager
from .agents import SCIExecutorAgent

# Legacy components (preserved as utilities)
from .executor import Executor
from .analysis import AnalysisAgent
from .planner import Planner

# Deprecated - kept for backward compatibility
from .scientist_loop import AIScientistLoop

__all__ = [
    # Data structures
    "Configuration",
    "Metrics",
    "Artifacts",
    "ExperimentRecord",
    "WorldModel",
    # New workflow components
    "SCIResearchWorkflow",
    "SCIStateManager",
    "SCIExecutorAgent",
    # Legacy utilities
    "Executor",
    "AnalysisAgent",
    "Planner",
    "AIScientistLoop",  # Deprecated
]
