from abm.agent import FBSAgent
from abm.agile import AgileSimulation
from abm.config import AgentConfig, FBSState


def test_agile_planning_phase() -> None:
    # Only leads participate in the planning phase.
    # We will simulate 1 team with 1 lead and 1 sub-module agent
    lead_config = AgentConfig(agent_id=1, module_id=1, sub_module_id=0) # 0 for lead
    agent_config = AgentConfig(agent_id=2, module_id=1, sub_module_id=1)

    lead = FBSAgent(lead_config)
    agent = FBSAgent(agent_config)

    # We configure 1 function to develop for the team
    sim = AgileSimulation([lead], [agent], functions_per_team=1)

    # Mock lead to advance quickly R->F
    lead.transition_matrix[FBSState.REQUIREMENTS] = [0.0, 1.0, 0.0, 0.0, 0.0]
    lead.transition_matrix[FBSState.FUNCTIONS] = [0.0, 0.0, 1.0, 0.0, 0.0]

    # Run planning phase
    sim._run_planning_phase()

    # Leads should finish R->F and stop.
    assert lead.current_state >= FBSState.FUNCTIONS

def test_agile_parallel_sprints() -> None:
    # Mocking two parallel teams, 1 function each
    config1 = AgentConfig(agent_id=1, module_id=1, sub_module_id=1)
    config2 = AgentConfig(agent_id=2, module_id=2, sub_module_id=2)

    agent1 = FBSAgent(config1)
    agent2 = FBSAgent(config2)

    sim = AgileSimulation([], [agent1, agent2], functions_per_team=1)
    sim.planning_complete = True

    # Agent 1 is fast: finishes function in 4 steps (no rework)
    agent1.transition_matrix = [
        [0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 0.0, 0.0, 1.0],
    ]

    # Agent 2 is slow: stays at R for a while
    agent2.transition_matrix = [
        [1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 0.0, 0.0, 1.0],
    ]

    # Run the sprints manually for a few steps to see parallel execution without synchronization
    for _ in range(4):
        sim.step()

    # Now force Agent 2 to finish
    agent2.transition_matrix[FBSState.REQUIREMENTS] = [0.0, 1.0, 0.0, 0.0, 0.0]
    while not sim.is_complete():
        sim.step()

    metrics = sim.get_metrics()
    assert metrics.total_time > 4.0

def test_agile_rework_backlog() -> None:
    # If a team hits rework, they add it to the backlog and finish it in a subsequent sprint.
    # In our simplified implementation, rework just extends the time spent on the function,
    # OR we can explicitly test pushing to a backlog queue.
    config1 = AgentConfig(agent_id=1, module_id=1, sub_module_id=1)
    agent = FBSAgent(config1)

    sim = AgileSimulation([], [agent], functions_per_team=1)
    sim.planning_complete = True

    # Create an agent that goes R->F->Be->S, reworks to Be, then finishes.
    class ReworkAgent(FBSAgent):
        def __init__(self, c: AgentConfig) -> None:
            super().__init__(c)
            self.seq = [
                (True, False), # R->F
                (True, False), # F->Be
                (True, False), # Be->S
                (False, True), # S->Be (rework!)
                (True, False), # Be->S
                (True, False), # S->D
            ]
            self.states = [
                FBSState.FUNCTIONS,
                FBSState.EXPECTED_BEHAVIOR,
                FBSState.STRUCTURE,
                FBSState.EXPECTED_BEHAVIOR,
                FBSState.STRUCTURE,
                FBSState.DOCUMENTATION,
            ]
            self.idx = 0

        def step(self, _u: float) -> tuple[bool, bool]:
            if self.idx < len(self.seq):
                adv, rew = self.seq[self.idx]
                self.current_state = self.states[self.idx]
                self.idx += 1
                return adv, rew
            return False, False

    sim.teams[1] = [ReworkAgent(config1)]

    sim.run()
    metrics = sim.get_metrics()
    assert metrics.total_time == 6.0
    assert metrics.effort_hours == 6.0
    assert metrics.rework_time == 1.0
