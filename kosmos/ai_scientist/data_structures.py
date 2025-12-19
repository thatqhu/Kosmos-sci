"""
Data Structures Module

Defines core data structures for the CIAS-X framework:
- Configuration: Experiment configuration
- Metrics: Performance metrics
- Artifacts: Experiment outputs
- ExperimentRecord: Complete experiment record
- WorldModel: Repository of all experiments
"""

import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from collections import defaultdict


@dataclass
class Configuration:
    """
    Experiment configuration for SCI reconstruction.

    Attributes:
        forward_config: Forward model configuration (compression, masks, etc.)
        recon_family: Reconstruction architecture family ("CIAS-Core", "CIAS-Core-ELP", etc.)
        recon_params: Architecture-specific parameters (layers, hidden dims, etc.)
        uq_scheme: Uncertainty quantification scheme ("Conformal", "Ensemble", "None")
        uq_params: UQ-specific parameters
        train_config: Training hyperparameters (epochs, lr, batch size, etc.)
    """
    forward_config: Dict[str, Any]
    recon_family: str
    recon_params: Dict[str, Any]
    uq_scheme: str
    uq_params: Dict[str, Any]
    train_config: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    def get_hash_key(self) -> str:
        """
        Generate a unique hash key for this configuration.

        Used to identify duplicate configurations. Two configurations with
        the same hash are considered identical.

        Returns:
            String hash key
        """
        import json
        import hashlib

        # Create a canonical representation
        # Sort dict keys to ensure consistent ordering
        config_dict = {
            'recon_family': self.recon_family,
            'recon_params': self._dict_to_sorted_str(self.recon_params),
            'uq_scheme': self.uq_scheme,
            'uq_params': self._dict_to_sorted_str(self.uq_params),
            'forward_config': self._dict_to_sorted_str(self.forward_config),
            'train_config': self._dict_to_sorted_str(self.train_config)
        }

        # Create JSON string with sorted keys
        canonical_str = json.dumps(config_dict, sort_keys=True)

        # Generate hash
        return hashlib.sha256(canonical_str.encode()).hexdigest()[:16]

    def _dict_to_sorted_str(self, d: Dict) -> str:
        """Convert dict to sorted string representation."""
        import json
        return json.dumps(d, sort_keys=True)

    def __hash__(self) -> int:
        """Make Configuration hashable for use in sets/dicts."""
        return int(self.get_hash_key(), 16)

    def __eq__(self, other) -> bool:
        """Check equality based on hash key."""
        if not isinstance(other, Configuration):
            return False
        return self.get_hash_key() == other.get_hash_key()


@dataclass
class Metrics:
    """
    Performance metrics for an experiment.

    Attributes:
        psnr: Peak Signal-to-Noise Ratio (dB)
        coverage: Uncertainty coverage probability
        latency: Inference latency (ms)
        calibration_error: Calibration error for UQ (optional)
        other_metrics: Additional custom metrics
    """
    psnr: float
    coverage: float
    latency: float
    calibration_error: Optional[float] = None
    other_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class Artifacts:
    """
    Experiment artifacts (saved outputs).

    Attributes:
        checkpoint: Model checkpoint path
        uq_params: Fitted UQ parameters
        train_log: Training log path
        eval_samples: Sample reconstruction paths
        fig_scripts: Figure generation scripts
    """
    checkpoint: str
    uq_params: Dict[str, Any]
    train_log: str
    eval_samples: List[str]
    fig_scripts: List[str]


@dataclass
class ExperimentRecord:
    """
    Complete record of a single experiment.

    Attributes:
        id: Unique experiment identifier
        config: Experiment configuration
        metrics: Performance metrics
        artifacts: Saved artifacts
        timestamp: Execution timestamp
    """
    id: str
    config: Configuration
    metrics: Metrics
    artifacts: Artifacts
    timestamp: str = ""

    def __post_init__(self):
        """Generate UUID if id is not provided."""
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class WorldModel:
    """
    World model storing all experiment history.

    The world model maintains:
    - Complete list of all experiments
    - Index structures for fast lookup by config attributes

    Attributes:
        experiments: List of all experiment records
        indices: Index structures (recon_family, uq_scheme, etc.)
    """
    experiments: List[ExperimentRecord] = field(default_factory=list)
    indices: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))

    def get_all_experiments(self) -> List[ExperimentRecord]:
        """Return all experiments in the world model."""
        return self.experiments
