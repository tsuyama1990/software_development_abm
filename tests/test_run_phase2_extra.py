from abm.config import AgentConfig
from abm.scaling import ScalingPenalties, ScalingPenaltiesConfig
from simulations.run_phase2 import Phase2Config, run_agile_single, run_waterfall_single


def test_run_single_methods() -> None:
    leads = [AgentConfig(agent_id=1, module_id=0, sub_module_id=0)]
    designers = [AgentConfig(agent_id=2, module_id=1, sub_module_id=1)]
    config = ScalingPenaltiesConfig(
        coordination_rate=0.3,
        communication_barrier_rate=0.3,
        resistant_agent_fraction=0.2,
        resistant_speed_factor=0.6,
    )
    penalties = ScalingPenalties(config)
    phase_config = Phase2Config()

    w_res = run_waterfall_single(leads, designers, penalties, phase_config)
    a_res = run_agile_single(leads, designers, penalties, phase_config)

    assert w_res.total_time > 0
    assert a_res.total_time > 0
