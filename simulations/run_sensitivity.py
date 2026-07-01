"""Phase 4 Sensitivity Analysis.

BLUEPRINT:
Data Flow:
- Uses `run_process` from `run_phase4.py` or sets up a direct simulation to measure
  Waterfall vs Agile total effort under varying AI configurations.
- Varies `AI_SPEED` (3.0 to 5.0) and `AI_REWORK` (2.0 to 4.0) over a 20x20 grid.
- Records which process mode (Waterfall or Agile) has lower effort.
- Saves the results as JSON or CSV for plotting.

Module Boundaries:
- Inputs: Simulation parameters (grid size).
- Outputs: A JSON file with grid results (coordinates and winners).
"""

import json
from pathlib import Path

import numpy as np

import abm.config
from abm.config import AIMode
from simulations.run_phase4 import run_process


def run_sensitivity_sweep() -> None:
    """Run a 20x20 sweep of ai_speed vs ai_rework and record the winner."""
    print("Running 2D sensitivity analysis. This will take a moment...")  # noqa: T201

    speed_range = np.linspace(3.0, 5.0, 20)
    rework_range = np.linspace(2.0, 4.0, 20)

    results = []

    # Temporarily store original constants
    orig_speed = abm.config.AI_SPEED
    orig_rework = abm.config.AI_REWORK

    try:
        for speed in speed_range:
            for rework in rework_range:
                # Override constants
                abm.config.AI_SPEED = float(speed)
                abm.config.AI_REWORK = float(rework)

                # Compare Waterfall vs Agile using AI_RAW
                # We use 1 run per cell to save time for this example,
                # though a full study might use Monte Carlo average.
                w_effort = run_process("Waterfall", AIMode.AI_RAW, runs=1)
                a_effort = run_process("Agile", AIMode.AI_RAW, runs=1)

                winner = "Waterfall" if w_effort < a_effort else "Agile"

                results.append({
                    "ai_speed": float(speed),
                    "ai_rework": float(rework),
                    "waterfall_effort": w_effort,
                    "agile_effort": a_effort,
                    "winner": winner,
                })
    finally:
        # Restore constants
        abm.config.AI_SPEED = orig_speed
        abm.config.AI_REWORK = orig_rework

    # Save results
    out_dir = Path("analysis")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "sensitivity_results.json"

    with out_file.open("w") as f:
        json.dump(results, f, indent=2)

    print(f"Sensitivity sweep complete. Results saved to {out_file}")  # noqa: T201


if __name__ == "__main__":
    run_sensitivity_sweep()
