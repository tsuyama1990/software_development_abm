
from abm.agent import FBSAgent
from abm.agile import AgileSimulation
from abm.config import AgentConfig
from abm.scaling import ScalingPenalties, ScalingPenaltiesConfig
from abm.waterfall import WaterfallSimulation


def test_coordination_delay() -> None:
    config = ScalingPenaltiesConfig(
        coordination_rate=0.5,
        communication_barrier_rate=0.3667,
        resistant_agent_fraction=0.20,
        resistant_speed_factor=0.60,
    )
    penalties = ScalingPenalties(config)

    # test baseline teams (12), base_delay = 8.0, rate = 0.5
    # 8.0 * (12/12) * 0.5 = 4.0
    delay = penalties.get_coordination_delay(n_teams=12, n_teams_baseline=12, base_delay=8.0)
    assert delay == 4.0

    # test larger teams (24)
    # 8.0 * (24/12) * 0.5 = 8.0
    delay2 = penalties.get_coordination_delay(n_teams=24, n_teams_baseline=12, base_delay=8.0)
    assert delay2 == 8.0

    # edge case zero baseline
    delay_zero = penalties.get_coordination_delay(n_teams=12, n_teams_baseline=0, base_delay=8.0)
    assert delay_zero == 0.0


def test_communication_delay_bounds() -> None:
    # Set to always trigger
    config = ScalingPenaltiesConfig(
        coordination_rate=0.3333,
        communication_barrier_rate=1.0,  # Always triggers
        resistant_agent_fraction=0.20,
        resistant_speed_factor=0.60,
    )
    penalties = ScalingPenalties(config)

    delays = [penalties.get_communication_delay(low_delay=1.0, high_delay=5.0) for _ in range(100)]
    assert all(1.0 <= d <= 5.0 for d in delays)

    # Set to never trigger
    config.communication_barrier_rate = 0.0
    penalties = ScalingPenalties(config)
    delays_zero = [
        penalties.get_communication_delay(low_delay=1.0, high_delay=5.0)
        for _ in range(100)
    ]
    assert all(d == 0.0 for d in delays_zero)


def test_agile_scaling_penalty_integration() -> None:
    leads = [AgentConfig(agent_id=1, module_id=0, sub_module_id=0)]
    designers = [AgentConfig(agent_id=2, module_id=1, sub_module_id=1)]

    # Run WITHOUT penalties
    sim_baseline = AgileSimulation(
        leads=[FBSAgent(c) for c in leads],
        agents=[FBSAgent(c) for c in designers],
        functions_per_team=2,
    )
    res_baseline = sim_baseline.run()

    # Run WITH extreme penalties
    config = ScalingPenaltiesConfig(
        coordination_rate=1.0,
        communication_barrier_rate=1.0,
        resistant_agent_fraction=1.0,  # Everyone resistant
        resistant_speed_factor=0.1,  # 90% slower
    )
    penalties = ScalingPenalties(config)

    # Modify config for resistance since AgileSimulation assumes this is pre-configured
    for c in designers + leads:
        c.is_resistant = True
        c.resistant_speed_factor = 0.1

    sim_penalized = AgileSimulation(
        leads=[FBSAgent(c) for c in leads],
        agents=[FBSAgent(c) for c in designers],
        functions_per_team=2,
        scaling_penalties=penalties,
        inter_team_meeting_hours=10.0,  # huge delay
        scrum_low_delay=1.0,
        scrum_high_delay=2.0,
        daily_scrum_interval=24,
    )
    res_penalized = sim_penalized.run()

    # Time should be strictly larger with extreme penalties
    assert res_penalized.total_time > res_baseline.total_time


def test_waterfall_scaling_penalty_integration() -> None:
    leads = [AgentConfig(agent_id=1, module_id=0, sub_module_id=0)]
    designers = [AgentConfig(agent_id=2, module_id=1, sub_module_id=1)]

    # Run WITHOUT penalties
    sim_baseline = WaterfallSimulation(
        agents=[FBSAgent(c) for c in leads + designers],
    )
    res_baseline = sim_baseline.run()

    # Run WITH extreme penalties
    config = ScalingPenaltiesConfig(
        coordination_rate=1.0,
        communication_barrier_rate=1.0,
        resistant_agent_fraction=0.0,  # Not applicable to waterfall
        resistant_speed_factor=1.0,
    )
    penalties = ScalingPenalties(config)

    sim_penalized = WaterfallSimulation(
        agents=[FBSAgent(c) for c in leads + designers],
        scaling_penalties=penalties,
        gate_review_hours=100.0,
        cascade_low_delay=10.0,
        cascade_high_delay=20.0,
        n_teams_baseline=1,
    )
    res_penalized = sim_penalized.run()

    # Time should be strictly larger with extreme penalties
    assert res_penalized.total_time > res_baseline.total_time
