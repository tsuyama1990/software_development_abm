"""Phase 4: AI Coding Dimension Simulation.

This module runs a 3-way comparison of 5 process models across 3 AI modes
(NO_AI, AI_RAW, AI_REACT) to evaluate how AI speedups and ReAct mitigation
change total effort and rework cascades.
"""

import statistics
from typing import Any

from abm.agent import FBSAgent
from abm.agile import AgileSimulation
from abm.config import AgentConfig, AIMode
from abm.hybrid import (
    Hybrid1Config,
    Hybrid1Simulation,
    Hybrid2Config,
    Hybrid2Simulation,
    Hybrid3Config,
    Hybrid3Simulation,
)
from abm.waterfall import WaterfallSimulation
from simulations.run_phase1 import build_program


def _set_ai_mode(configs: list[AgentConfig], ai_mode: AIMode) -> list[AgentConfig]:
    for c in configs:
        c.ai_mode = ai_mode
    return configs





def run_process(process_name: str, ai_mode: AIMode, runs: int = 5) -> float:
    """Run a specific process model under a specific AI mode and return average effort."""
    efforts = []

    for _ in range(runs):
        leads_cfg, designers_cfg = build_program()
        leads_cfg = _set_ai_mode(leads_cfg, ai_mode)
        designers_cfg = _set_ai_mode(designers_cfg, ai_mode)

        leads = [FBSAgent(c) for c in leads_cfg]
        designers = [FBSAgent(c) for c in designers_cfg]

        sim: Any

        if process_name == "Waterfall":
            sim = WaterfallSimulation(leads + designers)
        elif process_name == "Agile":
            sim = AgileSimulation(leads, designers, functions_per_team=10)
        elif process_name == "Hybrid 1":
            sim = Hybrid1Simulation(leads + designers, config=Hybrid1Config())
        elif process_name == "Hybrid 2":
            sim = Hybrid2Simulation(leads + designers, config=Hybrid2Config())
        elif process_name == "Hybrid 3":
            sim = Hybrid3Simulation(leads + designers, config=Hybrid3Config())
        else:
            msg = f"Unknown process: {process_name}"
            raise ValueError(msg)

        metrics = sim.run()
        efforts.append(float(metrics.effort_hours))

    return float(statistics.mean(efforts))


def main() -> None:
    """Run the 3-way comparison and print the Phase 4 Table."""
    processes = ["Waterfall", "Agile", "Hybrid 1", "Hybrid 2", "Hybrid 3"]
    modes = [AIMode.NO_AI, AIMode.AI_RAW, AIMode.AI_REACT]

    # fmt: off
    print("Phase 4: AI Coding Dimension Comparison")  # noqa: T201
    print(  # noqa: T201
        f"{'Process Mode':<15} | {'NO_AI effort':<14} | {'AI_RAW effort':<15} | "
        f"{'AI_REACT effort':<17} | {'Winner vs Agile+AI':<20}",
    )
    print("-" * 90)  # noqa: T201
    # fmt: on

    results = {}
    agile_ai_raw_effort = 0.0

    for process in processes:
        row = {}
        for mode in modes:
            effort = run_process(process, mode)
            row[mode] = effort
            if process == "Agile" and mode == AIMode.AI_RAW:
                agile_ai_raw_effort = effort
        results[process] = row

    for process in processes:
        no_ai = results[process][AIMode.NO_AI]
        ai_raw = results[process][AIMode.AI_RAW]
        ai_react = results[process][AIMode.AI_REACT]

        winner_text = ""
        if process == "Agile":
            winner_text = "(baseline)"
        else:
            winner = ai_react < agile_ai_raw_effort
            winner_text = "Yes" if winner else "No"

        # fmt: off
        print(  # noqa: T201
            f"{process:<15} | {no_ai:>12,.0f} h | {ai_raw:>13,.0f} h | "
            f"{ai_react:>15,.0f} h | {winner_text:>20}",
        )
        # fmt: on


if __name__ == "__main__":
    main()
