"""
Phase 5: Full Comparison Matrix (Agile vs Waterfall vs Hybrids + AI/ReAct).

BLUEPRINT:
Data Flow:
- Uses `concurrent.futures.ProcessPoolExecutor` to run 15 scenarios.
- Scenarios: 5 Process Modes (W, G, H1, H2, H3) x 3 AI Modes (A, B, C).
- Runs 10k Monte Carlo iterations per scenario (default, configurable).
- Gathers metrics (Time, Effort, Rework, Productivity, Rework Fraction).
- Tests the core hypothesis E(W-C) < E(G-B).
- Saves results to `results/phase5_summary.csv`.
- Generates final paper figures using `analysis/plots.py`.

Module Boundaries:
- Inputs: ABM configurations, Simulation logic.
- Outputs: Prints results, writes CSV, generates PNG figures.
"""

import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from abm.agent import FBSAgent
from abm.agile import AgileSimulation
from abm.config import AIMode
from abm.hybrid import (
    Hybrid1Config,
    Hybrid1Simulation,
    Hybrid2Config,
    Hybrid2Simulation,
    Hybrid3Config,
    Hybrid3Simulation,
)
from abm.metrics import MetricsCollector, RunMetrics
from abm.waterfall import WaterfallSimulation
from analysis.plots import plot_final_figures, plot_hypothesis_test
from analysis.statistics import hypothesis_test_waterfall_react_vs_agile_raw
from simulations.run_phase1 import build_program


def run_scenario(process_mode: str, ai_mode: AIMode, _seed: int) -> dict[str, float]:
    """Run a single Monte Carlo simulation for a specific process and AI mode."""
    leads_cfg, designers_cfg = build_program()

    for cfg in leads_cfg + designers_cfg:
        cfg.ai_mode = ai_mode

    leads = [FBSAgent(c) for c in leads_cfg]
    designers = [FBSAgent(c) for c in designers_cfg]
    all_agents = leads + designers

    sim: Any

    if process_mode == "Waterfall":
        sim = WaterfallSimulation(all_agents)
    elif process_mode == "Agile":
        sim = AgileSimulation(leads, designers, functions_per_team=10)
    elif process_mode == "Hybrid1":
        sim = Hybrid1Simulation(all_agents, config=Hybrid1Config())
    elif process_mode == "Hybrid2":
        sim = Hybrid2Simulation(all_agents, config=Hybrid2Config())
    elif process_mode == "Hybrid3":
        sim = Hybrid3Simulation(all_agents, config=Hybrid3Config(), total_functions=120)
    else:
        msg = f"Unknown process mode: {process_mode}"
        raise ValueError(msg)

    metrics = sim.run()

    return {
        "total_time": metrics.total_time,
        "effort_hours": metrics.effort_hours,
        "rework_time": metrics.rework_time,
    }


def run_all_scenarios(num_runs: int) -> tuple[dict[str, dict[str, Any]], list[float], list[float]]:
    """Run all simulations and return stats along with raw data for testing."""
    process_modes = ["Waterfall", "Agile", "Hybrid1", "Hybrid2", "Hybrid3"]
    ai_modes = [AIMode.NO_AI, AIMode.AI_RAW, AIMode.AI_REACT]

    mode_codes = {
        "Waterfall": "W",
        "Agile": "G",
        "Hybrid1": "H1",
        "Hybrid2": "H2",
        "Hybrid3": "H3",
    }

    ai_codes = {
        AIMode.NO_AI: "A",
        AIMode.AI_RAW: "B",
        AIMode.AI_REACT: "C",
    }

    scenarios = [(p, a) for p in process_modes for a in ai_modes]

    all_results: dict[str, dict[str, Any]] = {}
    w_react_effort: list[float] = []
    g_raw_effort: list[float] = []

    with ProcessPoolExecutor() as executor:
        for p_mode, a_mode in scenarios:
            scenario_name = f"{mode_codes[p_mode]}-{ai_codes[a_mode]}"
            print(f"Starting {scenario_name} ({p_mode} + {a_mode.value})...")

            futures = [executor.submit(run_scenario, p_mode, a_mode, i) for i in range(num_runs)]
            collector = MetricsCollector()

            for future in as_completed(futures):
                res = future.result()
                collector.add_run(
                    RunMetrics(
                        total_time=res["total_time"],
                        effort_hours=res["effort_hours"],
                        rework_time=res["rework_time"],
                    ),
                )
                if scenario_name == "W-C":
                    w_react_effort.append(res["effort_hours"])
                elif scenario_name == "G-B":
                    g_raw_effort.append(res["effort_hours"])

            stats = collector.get_statistics()
            mean_time = stats["total_time_mean"]
            mean_effort = stats["effort_hours_mean"]
            mean_rework = stats["rework_time_mean"]

            all_results[scenario_name] = {
                "time": mean_time,
                "effort": mean_effort,
                "rework": mean_rework,
                "productivity": 120 / mean_effort if mean_effort > 0 else 0,
                "rework_fraction": (mean_rework / mean_time * 100) if mean_time > 0 else 0,
            }
            print(
                f"  Completed {scenario_name}: Effort={mean_effort:,.0f}h, Time={mean_time:,.0f}h",
            )

    return all_results, w_react_effort, g_raw_effort


def main(num_runs: int = 10000) -> None:
    """Run the Phase 5 Monte Carlo simulations."""
    print(f"Running Phase 5 full comparison matrix with {num_runs} MC runs per scenario...")

    all_results, w_react_effort, g_raw_effort = run_all_scenarios(num_runs)

    # Save to CSV
    Path("results").mkdir(exist_ok=True)
    csv_file = Path("results/phase5_summary.csv")
    with csv_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Scenario",
            "Effort (h)",
            "Time (h)",
            "Rework (h)",
            "Productivity (func/h)",
            "Rework Fraction (%)",
        ])
        for scenario, metrics in all_results.items():
            writer.writerow([
                scenario,
                f"{metrics['effort']:.2f}",
                f"{metrics['time']:.2f}",
                f"{metrics['rework']:.2f}",
                f"{metrics['productivity']:.4f}",
                f"{metrics['rework_fraction']:.2f}",
            ])
    print(f"\nResults saved to {csv_file}")

    # Perform Hypothesis Test
    print("\n" + "="*50)
    print("HYPOTHESIS TEST: Waterfall+ReAct vs Agile+RAW")
    print("H1: E(W-C) < E(G-B)")
    print("="*50)

    hyp_res = hypothesis_test_waterfall_react_vs_agile_raw(w_react_effort, g_raw_effort)
    print(f"Waterfall+ReAct (W-C) Mean Effort: {hyp_res['mean_w_react']:,.0f}h")
    print(f"Agile+RAW (G-B) Mean Effort:       {hyp_res['mean_g_raw']:,.0f}h")
    print(f"Difference:                        {hyp_res['pct_difference']:+.1f}%")
    print(f"p-value:                           {hyp_res['p_value']:.4e}")
    print(f"Cohen's d:                         {hyp_res['cohens_d']:.2f}")
    if hyp_res["hypothesis_confirmed"]:
        print("\nCONCLUSION: Hypothesis CONFIRMED. W-C takes significantly less effort than G-B.")
    else:
        print("\nCONCLUSION: Hypothesis REFUTED.")
        print("W-C does not take significantly less effort than G-B.")

    # Generate final figures
    print("\nGenerating final paper figures...")
    plot_final_figures(all_results)

    plot_hypothesis_test(
        w_react_effort,
        g_raw_effort,
        hyp_res["p_value"],
        hyp_res["pct_difference"],
        filename="results/figures/fig3_hypothesis_test.png",
    )
    print("Figures saved to results/figures/")

if __name__ == "__main__":
    runs = 10000
    if len(sys.argv) > 1 and sys.argv[1] == "--fast":
        runs = 10
    main(runs)
