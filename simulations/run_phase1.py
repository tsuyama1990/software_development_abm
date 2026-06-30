"""Phase 1: Foundation (Reproduce Bott & Mesmer 2019).

BLUEPRINT:
Data Flow:
- Configures 101 agents: 1 Program Lead, 4 Module Leads,
  and 96 Sub-Module Designers (12 teams of 8).
- Each sub-module has 10 functions to develop (120 total).
- Uses `MetricsCollector` to run `WaterfallSimulation` and
  `AgileSimulation` 10,000 times (or smaller for fast mode).
- Outputs summary statistics and ratio comparisons (Waterfall vs Agile) to standard output.

Module Boundaries:
- Inputs: ABM configuration (Agents, Simulation Logic).
- Outputs: Prints metrics matching Table 2 (Bott & Mesmer).
"""

import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

from abm.agent import FBSAgent
from abm.agile import AgileSimulation
from abm.config import AgentConfig
from abm.metrics import MetricsCollector, RunMetrics
from abm.waterfall import WaterfallSimulation


def build_program() -> tuple[list[AgentConfig], list[AgentConfig]]:
    """Build the 101-agent team structure as defined in the paper.

    - 1 Program Lead
    - 4 Module Leads
    - 12 Sub-module teams (each with 8 designers).

    Returns:
        tuple[list[AgentConfig], list[AgentConfig]]: (leads, designers)

    """
    leads = []
    designers = []

    agent_id = 1

    # Program Lead (module=0, sub_module=0)
    leads.append(AgentConfig(agent_id=agent_id, module_id=0, sub_module_id=0))
    agent_id += 1

    # 4 Module Leads (module=1..4, sub_module=0)
    for m in range(1, 5):
        leads.append(AgentConfig(agent_id=agent_id, module_id=m, sub_module_id=0))
        agent_id += 1

    # 12 Sub-modules, 8 designers each
    # Module 1: 3 sub-modules (1.1, 1.2, 1.3)
    # Module 2: 3 sub-modules (2.1, 2.2, 2.3)
    # Module 3: 2 sub-modules (3.1, 3.2)
    # Module 4: 4 sub-modules (4.1, 4.2, 4.3, 4.4)
    sub_modules = {
        1: [1, 2, 3],
        2: [4, 5, 6],
        3: [7, 8],
        4: [9, 10, 11, 12],
    }

    for m, sub_list in sub_modules.items():
        for sub_id in sub_list:
            for _ in range(8):
                designers.append(
                    AgentConfig(agent_id=agent_id, module_id=m, sub_module_id=sub_id),
                )
                agent_id += 1

    return leads, designers


def run_waterfall_single(_seed: int) -> dict[str, float]:
    """Run a single waterfall simulation and return the metrics dictionary."""
    leads, designers = build_program()
    # In waterfall, ALL agents participate (though paper says leads only plan,
    # but the mechanics are all agents go through phases synchronously).
    # We will include all 101 agents in the waterfall run.
    agents = [FBSAgent(c) for c in leads + designers]

    sim = WaterfallSimulation(agents)
    metrics = sim.run()

    return {
        "total_time": metrics.total_time,
        "effort_hours": metrics.effort_hours,
        "rework_time": metrics.rework_time,
    }


def run_agile_single(_seed: int) -> dict[str, float]:
    """Run a single agile simulation and return the metrics dictionary."""
    leads_cfg, designers_cfg = build_program()
    leads = [FBSAgent(c) for c in leads_cfg]
    designers = [FBSAgent(c) for c in designers_cfg]

    sim = AgileSimulation(leads, designers, functions_per_team=10)
    metrics = sim.run()

    return {
        "total_time": metrics.total_time,
        "effort_hours": metrics.effort_hours,
        "rework_time": metrics.rework_time,
    }


def run_monte_carlo(num_runs: int = 10000) -> None:
    """Run Monte Carlo simulation for both methodologies and compare."""
    print(f"Running {num_runs} Monte Carlo iterations... (this may take a while)")

    # We will run them in parallel to save time
    waterfall_collector = MetricsCollector()
    agile_collector = MetricsCollector()

    with ProcessPoolExecutor() as executor:
        # Submit waterfall tasks
        waterfall_futures = [executor.submit(run_waterfall_single, i) for i in range(num_runs)]

        for idx, future in enumerate(as_completed(waterfall_futures)):
            res = future.result()
            waterfall_collector.add_run(
                RunMetrics(
                    total_time=res["total_time"],
                    effort_hours=res["effort_hours"],
                    rework_time=res["rework_time"],
                ),
            )
            if (idx + 1) % (num_runs // 10) == 0:
                print(f"Waterfall: {idx + 1}/{num_runs} completed")

        # Submit agile tasks
        agile_futures = [executor.submit(run_agile_single, i) for i in range(num_runs)]

        for idx, future in enumerate(as_completed(agile_futures)):
            res = future.result()
            agile_collector.add_run(
                RunMetrics(
                    total_time=res["total_time"],
                    effort_hours=res["effort_hours"],
                    rework_time=res["rework_time"],
                ),
            )
            if (idx + 1) % (num_runs // 10) == 0:
                print(f"Agile: {idx + 1}/{num_runs} completed")

    w_stats = waterfall_collector.get_statistics()
    a_stats = agile_collector.get_statistics()

    print("\n" + "="*50)
    print("RESULTS COMPARISON (Agile vs Waterfall)")
    print("="*50)

    metrics = ["effort_hours", "total_time", "rework_time"]
    labels = ["Effort Hours", "Total Time", "Rework Time"]

    for metric, label in zip(metrics, labels, strict=True):
        w_mean = w_stats[f"{metric}_mean"]
        w_std = w_stats[f"{metric}_std"]
        a_mean = a_stats[f"{metric}_mean"]
        a_std = a_stats[f"{metric}_std"]

        diff_pct = ((a_mean - w_mean) / w_mean) * 100

        print(f"\n{label}:")
        print(f"  Waterfall: {w_mean:,.0f} h (SD={w_std:,.0f})")
        print(f"  Agile:     {a_mean:,.0f} h (SD={a_std:,.0f})")
        print(f"  Difference: {diff_pct:+.0f}%")


if __name__ == "__main__":
    # If a fast argument is passed, do fewer runs for testing
    NUM_RUNS = 10000
    if len(sys.argv) > 1 and sys.argv[1] == "--fast":
        NUM_RUNS = 100

    run_monte_carlo(NUM_RUNS)
