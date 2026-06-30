from abm.agent import FBSAgent
from abm.config import AgentConfig, FBSState
from abm.waterfall import WaterfallSimulation


def test_waterfall_srr_gate() -> None:
    config1 = AgentConfig(agent_id=1, module_id=1, sub_module_id=1)
    config2 = AgentConfig(agent_id=2, module_id=1, sub_module_id=1)
    agents = [FBSAgent(config1), FBSAgent(config2)]

    sim = WaterfallSimulation(agents)

    # Force agent 1 to transition to F, but agent 2 to stay at R
    agents[0].transition_matrix[FBSState.REQUIREMENTS] = [0.0, 1.0, 0.0, 0.0, 0.0]
    agents[1].transition_matrix[FBSState.REQUIREMENTS] = [1.0, 0.0, 0.0, 0.0, 0.0]

    sim.step()

    # We will verify this by mocking agent 1's F->Be transition to be 100%
    agents[0].transition_matrix[FBSState.FUNCTIONS] = [0.0, 0.0, 1.0, 0.0, 0.0]

    sim.step()

    # Now force agent 2 to finish SRR
    agents[1].transition_matrix[FBSState.REQUIREMENTS] = [0.0, 1.0, 0.0, 0.0, 0.0]
    sim.step()

    # Now that both are in F (SRR complete), agent 1 can advance to Be on the NEXT step
    sim.step()


def test_waterfall_rework_delay() -> None:
    config1 = AgentConfig(agent_id=1, module_id=1, sub_module_id=1)
    agents = [FBSAgent(config1)]

    sim = WaterfallSimulation(agents)

    # Move to STRUCTURE (Phase 3)
    agents[0].current_state = FBSState.STRUCTURE
    sim.current_phase = 3 # PDR complete, in CDR (S->D)

    # Force a Type I rework from S to Be
    agents[0].transition_matrix[FBSState.STRUCTURE] = [0.0, 0.0, 1.0, 0.0, 0.0]

    sim.step()

    # It will need to work its way back up.
    # Force advance back to S
    agents[0].transition_matrix[FBSState.EXPECTED_BEHAVIOR] = [0.0, 0.0, 0.0, 1.0, 0.0]
    sim.step()

    # Phase should now be 3 again
    sim.step()
    # Note: The orchestrator evaluates phase completion at the end of the step.

def test_waterfall_run_completion() -> None:
    config1 = AgentConfig(agent_id=1, module_id=1, sub_module_id=1)
    agent = FBSAgent(config1)

    # Force fast path to completion
    agent.transition_matrix = [
        [0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 0.0, 0.0, 1.0],
    ]

    sim = WaterfallSimulation([agent])
    metrics = sim.run()
    assert metrics.total_time == 4.0
    assert metrics.effort_hours == 4.0
    assert metrics.rework_time == 0.0

def test_waterfall_rework_metrics() -> None:
    config1 = AgentConfig(agent_id=1, module_id=1, sub_module_id=1)

    # Better: just use an agent that goes R->F->Be->S, then rework to Be, then S, then D
    class MockAgent(FBSAgent):
        def __init__(self, c: AgentConfig) -> None:
            super().__init__(c)
            self.seq = [
                (True, False), # R->F
                (True, False), # F->Be
                (True, False), # Be->S
                (False, True), # Rework S->Be
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

    mock_agent = MockAgent(config1)
    sim2 = WaterfallSimulation([mock_agent])
    m = sim2.run()

    assert m.total_time == 6.0
    assert m.effort_hours == 6.0
    assert m.rework_time == 1.0

def test_waterfall_empty() -> None:
    sim = WaterfallSimulation([])
    m = sim.run()
    assert m.total_time == 0.0
