"""
Scaling Penalties Module.

BLUEPRINT:
Data Flow:
- Configuration is provided via `ScalingPenaltiesConfig` (a Pydantic model).
- The `ScalingPenalties` class uses the config to compute scaling delays:
  - `get_coordination_delay`: Computes a delay proportional to the number of teams.
  - `get_communication_delay`: Computes a random delay based on a Bernoulli trial.

Module Boundaries:
- Inputs: `ScalingPenaltiesConfig` for initialization.
- Outputs: Float representing delay hours.

Key Interfaces:
- `ScalingPenaltiesConfig`: Data model for configuration.
- `ScalingPenalties`: Provides methods `get_coordination_delay` and `get_communication_delay`.
"""

import numpy as np
from pydantic import BaseModel, ConfigDict


class ScalingPenaltiesConfig(BaseModel):
    """Configuration for scaling penalties."""

    model_config = ConfigDict(extra="forbid", strict=True)

    coordination_rate: float
    communication_barrier_rate: float
    resistant_agent_fraction: float
    resistant_speed_factor: float


class ScalingPenalties:
    """Computes scaling penalties based on Matcha & Kumar (2025) survey data."""

    def __init__(self, config: ScalingPenaltiesConfig) -> None:
        """Initialize the scaling penalties calculator."""
        self.config = config

    def get_coordination_delay(
        self, n_teams: int, n_teams_baseline: int, base_delay: float,
    ) -> float:
        """
        Calculate the coordination delay.

        coordination_delay = base_delay * (n_teams / n_teams_baseline) * coordination_rate

        Args:
            n_teams: Number of teams coordinating.
            n_teams_baseline: Baseline number of teams.
            base_delay: Base delay cost in hours.

        Returns:
            The calculated coordination delay.

        """
        if n_teams_baseline <= 0:
            return 0.0
        return base_delay * (n_teams / n_teams_baseline) * self.config.coordination_rate

    def get_communication_delay(self, low_delay: float, high_delay: float) -> float:
        """
        Calculate the communication barrier delay.

        delay ~ Bernoulli(communication_barrier_rate) * Uniform(low_delay, high_delay)

        Args:
            low_delay: Lower bound for the delay.
            high_delay: Upper bound for the delay.

        Returns:
            The calculated communication delay.

        """
        rng = np.random.default_rng()
        # Bernoulli trial
        if rng.random() < self.config.communication_barrier_rate:
            return float(rng.uniform(low_delay, high_delay))
        return 0.0
