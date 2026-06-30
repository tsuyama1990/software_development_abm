import math
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from pydantic import BaseModel, ConfigDict

from abm.agent import FBSAgent
from abm.agile import AgileSimulation
from abm.config import AgentConfig
from abm.metrics import MetricsCollector, RunMetrics
from abm.scaling import ScalingPenalties, ScalingPenaltiesConfig
from abm.waterfall import WaterfallSimulation


class Phase2Config(BaseModel):
    """Configuration for Phase 2 simulation parameters."""

    model_config = ConfigDict(extra="forbid", strict=True)

    team_sizes: list[int] = [4, 8, 12, 20, 32, 50]
    n_teams_baseline: int = 12
    designers_per_team: int = 8
    functions_per_team: int = 10

    # Waterfall specifics
    gate_review_hours: float = 8.0
    cascade_low_delay: float = 1.0
    cascade_high_delay: float = 8.0

    # Agile specifics
    inter_team_meeting_hours: float = 2.0
    scrum_low_delay: float = 0.5
    scrum_high_delay: float = 2.0
    scrum_velocity_modifier: float = 1.0
    daily_scrum_interval: int = 24


def build_program(
    n_submodule_teams: int, scaling_config: ScalingPenaltiesConfig, phase_config: Phase2Config,
) -> tuple[list[AgentConfig], list[AgentConfig]]:
    """Build the agent program for a given scale with resistance applied."""
    leads = []
    designers = []

    # Number of modules derived roughly (e.g., each module has ~3 teams as in Phase 1)
    n_modules = max(1, math.ceil(n_submodule_teams / 3))

    agent_id = 1
    rng = np.random.default_rng()

    # Program Lead
    leads.append(AgentConfig(
        agent_id=agent_id,
        module_id=0,
        sub_module_id=0,
    ))
    agent_id += 1

    # Module Leads
    for m in range(1, n_modules + 1):
        leads.append(AgentConfig(
            agent_id=agent_id,
            module_id=m,
            sub_module_id=0,
        ))
        agent_id += 1

    # Sub-modules
    for team_idx in range(n_submodule_teams):
        m = (team_idx % n_modules) + 1
        sub_id = team_idx + 1

        for _ in range(phase_config.designers_per_team):
            # Decide if resistant based on phase 2 configuration
            is_resistant = rng.random() < scaling_config.resistant_agent_fraction

            designers.append(
                AgentConfig(
                    agent_id=agent_id,
                    module_id=m,
                    sub_module_id=sub_id,
                    is_resistant=is_resistant,
                    resistant_speed_factor=scaling_config.resistant_speed_factor,
                ),
            )
            agent_id += 1

    return leads, designers


def run_waterfall_single(
    leads_cfg: list[AgentConfig],
    designers_cfg: list[AgentConfig],
    penalties: ScalingPenalties,
    phase_config: Phase2Config,
) -> RunMetrics:
    agents = [FBSAgent(c) for c in leads_cfg + designers_cfg]
    sim = WaterfallSimulation(
        agents=agents,
        scaling_penalties=penalties,
        gate_review_hours=phase_config.gate_review_hours,
        cascade_low_delay=phase_config.cascade_low_delay,
        cascade_high_delay=phase_config.cascade_high_delay,
        n_teams_baseline=phase_config.n_teams_baseline,
    )
    return sim.run()


def run_agile_single(
    leads_cfg: list[AgentConfig],
    designers_cfg: list[AgentConfig],
    penalties: ScalingPenalties,
    phase_config: Phase2Config,
) -> RunMetrics:
    leads = [FBSAgent(c) for c in leads_cfg]
    designers = [FBSAgent(c) for c in designers_cfg]
    sim = AgileSimulation(
        leads=leads,
        agents=designers,
        functions_per_team=phase_config.functions_per_team,
        scaling_penalties=penalties,
        inter_team_meeting_hours=phase_config.inter_team_meeting_hours,
        scrum_low_delay=phase_config.scrum_low_delay,
        scrum_high_delay=phase_config.scrum_high_delay,
        scrum_velocity_modifier=phase_config.scrum_velocity_modifier,
        daily_scrum_interval=phase_config.daily_scrum_interval,
        n_teams_baseline=phase_config.n_teams_baseline,
    )
    return sim.run()


def run_sweep(
    num_runs: int = 100, phase_config: Phase2Config | None = None,
) -> list[dict[str, float]]:
    if phase_config is None:
        phase_config = Phase2Config()

    config = ScalingPenaltiesConfig(
        coordination_rate=0.3333,
        communication_barrier_rate=0.3667,
        resistant_agent_fraction=0.20,
        resistant_speed_factor=0.60,
    )
    penalties = ScalingPenalties(config)

    results = []

    for n_teams in phase_config.team_sizes:
        print(f"Running simulation for {n_teams} teams...")

        w_collector = MetricsCollector()
        a_collector = MetricsCollector()

        # For smaller number of runs (or sweep), using basic loop is sometimes better,
        # but ProcessPoolExecutor can speed it up.
        with ProcessPoolExecutor() as executor:
            # We must pass configs because FBSAgent is instantiated per run to reset state
            w_futures = []
            a_futures = []
            for _ in range(num_runs):
                leads_cfg, designers_cfg = build_program(n_teams, config, phase_config)
                w_futures.append(
                    executor.submit(
                        run_waterfall_single, leads_cfg, designers_cfg, penalties, phase_config,
                    ),
                )
                a_futures.append(
                    executor.submit(
                        run_agile_single, leads_cfg, designers_cfg, penalties, phase_config,
                    ),
                )

            for future in as_completed(w_futures):
                w_collector.add_run(future.result())

            for future in as_completed(a_futures):
                a_collector.add_run(future.result())

        w_stats = w_collector.get_statistics()
        a_stats = a_collector.get_statistics()

        results.append({
            "n_submodule_teams": float(n_teams),
            "waterfall_total_time": w_stats["total_time_mean"],
            "agile_total_time": a_stats["total_time_mean"],
            "waterfall_effort": w_stats["effort_hours_mean"],
            "agile_effort": a_stats["effort_hours_mean"],
            "agile_advantage": w_stats["total_time_mean"] / a_stats["total_time_mean"],
        })

        adv = results[-1]["agile_advantage"]
        w_t = w_stats["total_time_mean"]
        a_t = a_stats["total_time_mean"]
        print(f"  Advantage: {adv:.2f}x (Waterfall: {w_t:.0f}h, Agile: {a_t:.0f}h)")

    return results

if __name__ == "__main__":
    import sys
    runs = 100
    if len(sys.argv) > 1 and sys.argv[1] == "--fast":
        runs = 10

    run_sweep(runs)
