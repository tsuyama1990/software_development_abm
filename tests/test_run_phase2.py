"""Tests for the Phase 2 simulations runner."""

from abm.scaling import ScalingPenaltiesConfig
from simulations.run_phase2 import Phase2Config, build_program, run_sweep


def test_build_program_counts() -> None:
    """Ensure build_program correctly instantiates agent configs."""
    scaling_config = ScalingPenaltiesConfig(
        coordination_rate=0.3333,
        communication_barrier_rate=0.3667,
        resistant_agent_fraction=0.20,
        resistant_speed_factor=0.60,
    )
    phase_config = Phase2Config(
        designers_per_team=4,
    )

    leads, designers = build_program(
        n_submodule_teams=3,
        scaling_config=scaling_config,
        phase_config=phase_config,
    )

    # 1 program lead, 1 module lead (since 3 teams / 3 = 1 module)
    assert len(leads) == 2
    # 3 teams * 4 designers = 12 designers
    assert len(designers) == 12


def test_run_sweep_small() -> None:
    """Ensure run_sweep can execute a tiny configuration without errors."""
    phase_config = Phase2Config(
        team_sizes=[4],
        designers_per_team=2,
        functions_per_team=2,
    )
    results = run_sweep(num_runs=1, phase_config=phase_config)

    assert len(results) == 1
    assert "agile_advantage" in results[0]
    assert results[0]["n_submodule_teams"] == 4.0
    assert results[0]["waterfall_total_time"] > 0
