"""
Run Phase 3: Hybrid Models simulation.

This script runs the 5 process modes (Waterfall, Agile, Hybrid 1, Hybrid 2, Hybrid 3)
and prints a comparison table of Time, Effort, and Rework metrics to verify they match
the expected theoretical hierarchy.
"""

import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

from abm.agent import FBSAgent
from abm.agile import AgileSimulation
from abm.config import AgentConfig
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


def build_agents(
    num_teams: int,
    designers_per_team: int,
) -> tuple[list[AgentConfig], list[AgentConfig]]:
    """Build the agent configurations for a given scale."""
    leads = [AgentConfig(agent_id=1, module_id=0, sub_module_id=0)]
    designers = []
    agent_id = 2
    for team_idx in range(1, num_teams + 1):
        for _ in range(designers_per_team):
            designers.append(AgentConfig(agent_id=agent_id, module_id=1, sub_module_id=team_idx))
            agent_id += 1
    return leads, designers


def run_waterfall(designers_cfg: list[AgentConfig]) -> dict[str, float]:
    """Run pure Waterfall simulation."""
    agents = [FBSAgent(c) for c in designers_cfg]
    sim = WaterfallSimulation(agents)
    metrics = sim.run()
    return {
        "time": metrics.total_time,
        "effort": metrics.effort_hours,
        "rework": metrics.rework_time,
    }


def run_agile(
    leads_cfg: list[AgentConfig], designers_cfg: list[AgentConfig],
) -> dict[str, float]:
    """Run pure Agile simulation."""
    leads = [FBSAgent(c) for c in leads_cfg]
    designers = [FBSAgent(c) for c in designers_cfg]
    sim = AgileSimulation(leads, designers, functions_per_team=10)
    metrics = sim.run()
    return {
        "time": metrics.total_time,
        "effort": metrics.effort_hours,
        "rework": metrics.rework_time,
    }


def run_hybrid1(designers_cfg: list[AgentConfig]) -> dict[str, float]:
    """Run Hybrid 1 simulation."""
    agents = [FBSAgent(c) for c in designers_cfg]
    sim = Hybrid1Simulation(agents, Hybrid1Config(), functions_per_team=10)
    metrics = sim.run()
    return {
        "time": metrics.total_time,
        "effort": metrics.effort_hours,
        "rework": metrics.rework_time,
    }


def run_hybrid2(designers_cfg: list[AgentConfig]) -> dict[str, float]:
    """Run Hybrid 2 simulation."""
    agents = [FBSAgent(c) for c in designers_cfg]
    config = Hybrid2Config(waterfall_fraction=0.5, agile_fraction=0.5, integration_coupling=0.15)
    sim = Hybrid2Simulation(agents, config, functions_per_team=10)
    metrics = sim.run()
    return {
        "time": metrics.total_time,
        "effort": metrics.effort_hours,
        "rework": metrics.rework_time,
    }


def run_hybrid3(designers_cfg: list[AgentConfig]) -> dict[str, float]:
    """Run Hybrid 3 simulation."""
    agents = [FBSAgent(c) for c in designers_cfg]
    config = Hybrid3Config(cycle_length_hours_min=320, cycle_length_hours_max=480)
    total_funcs = 10 * len({c.sub_module_id for c in designers_cfg})
    sim = Hybrid3Simulation(agents, config, total_functions=total_funcs)
    metrics = sim.run()
    return {
        "time": metrics.total_time,
        "effort": metrics.effort_hours,
        "rework": metrics.rework_time,
    }


def run_all(num_runs: int = 10) -> None:
    """Run simulations for all process modes and print comparison."""
    num_teams = 12
    designers_per_team = 8


    print(f"Running {num_runs} simulations...")

    results: dict[str, MetricsCollector] = {
        "Waterfall": MetricsCollector(),
        "Agile": MetricsCollector(),
        "Hybrid 1": MetricsCollector(),
        "Hybrid 2": MetricsCollector(),
        "Hybrid 3": MetricsCollector(),
    }

    with ProcessPoolExecutor() as executor:
        futures = []
        for _ in range(num_runs):
            leads_cfg, designers_cfg = build_agents(num_teams, designers_per_team)
            futures.append(("Waterfall", executor.submit(run_waterfall, designers_cfg)))
            futures.append(("Agile", executor.submit(run_agile, leads_cfg, designers_cfg)))
            futures.append(("Hybrid 1", executor.submit(run_hybrid1, designers_cfg)))
            futures.append(("Hybrid 2", executor.submit(run_hybrid2, designers_cfg)))
            futures.append(("Hybrid 3", executor.submit(run_hybrid3, designers_cfg)))

        # Use simple map pattern since we need the names
        future_to_name = {f: name for name, f in futures}
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            res = future.result()
            rm = RunMetrics(
                total_time=res["time"],
                effort_hours=res["effort"],
                rework_time=res["rework"],
            )
            results[name].add_run(rm)

    print("\n" + "=" * 80)
    print(
        f"{'Process Mode':<15} | "
        f"{'Total Time (h)':<15} | "
        f"{'Effort (h)':<15} | "
        f"{'Rework (h)':<15}",
    )
    print("-" * 80)

    summary = {}
    for name, collector in results.items():
        stats = collector.get_statistics()
        summary[name] = stats
        print(
            f"{name:<15} | "
            f"{stats['total_time_mean']:<15.1f} | "
            f"{stats['effort_hours_mean']:<15.1f} | "
            f"{stats['rework_time_mean']:<15.1f}",
        )

    print("=" * 80 + "\n")

    times = [(k, v["total_time_mean"]) for k, v in summary.items()]
    times.sort(key=lambda x: x[1])
    print(f"Time Order (Fastest to Slowest): {' < '.join(k for k, _ in times)}")

if __name__ == "__main__":
    runs_to_do = 100
    if len(sys.argv) > 1 and sys.argv[1] == "--fast":
        runs_to_do = 10
    run_all(runs_to_do)
