"""
Metrics Module for the Software Development ABM.

BLUEPRINT:
Data Flow:
- Each simulation run (Waterfall or Agile) outputs a `RunMetrics` object.
- `MetricsCollector` aggregates these metrics across Monte Carlo runs.
- Means and standard deviations are computed to compare against paper targets.

Module Boundaries:
- Inputs: Simulation run results.
- Outputs: Aggregated statistics dictionary.

Key Interfaces:
- `RunMetrics`: Pydantic model for individual run data.
- `MetricsCollector`: Accumulates and computes stats.
- `MonteCarloRunner`: Orchestrates multiple runs (to be implemented).
"""

import numpy as np
from pydantic import BaseModel, ConfigDict


class RunMetrics(BaseModel):
    """Data from a single simulation run."""

    model_config = ConfigDict(extra="forbid", strict=True)

    total_time: float
    effort_hours: float
    rework_time: float


class MetricsCollector:
    """Collects metrics across multiple simulation runs and computes statistics."""

    def __init__(self) -> None:
        """Initialize an empty collector."""
        self.runs: list[RunMetrics] = []

    def add_run(self, metrics: RunMetrics) -> None:
        """Add a run to the collector."""
        self.runs.append(metrics)

    def get_statistics(self) -> dict[str, float]:
        """
        Compute mean and std dev for all collected metrics.

        Returns empty dictionary if no runs are collected.
        """
        if not self.runs:
            return {}

        total_times = [r.total_time for r in self.runs]
        effort_hours = [r.effort_hours for r in self.runs]
        rework_times = [r.rework_time for r in self.runs]

        return {
            "total_time_mean": float(np.mean(total_times)),
            "total_time_std": float(
                np.std(total_times, ddof=1) if len(total_times) > 1 else 0.0,
            ),
            "effort_hours_mean": float(np.mean(effort_hours)),
            "effort_hours_std": float(
                np.std(effort_hours, ddof=1) if len(effort_hours) > 1 else 0.0,
            ),
            "rework_time_mean": float(np.mean(rework_times)),
            "rework_time_std": float(
                np.std(rework_times, ddof=1) if len(rework_times) > 1 else 0.0,
            ),
        }
