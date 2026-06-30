from abm.agent import FBSAgent
from abm.config import AgentConfig, FBSState


def test_agent_initialization() -> None:
    config = AgentConfig(agent_id=1, module_id=2, sub_module_id=3)
    agent = FBSAgent(config)

    # Check that transition matrix is initialized correctly based on mean/high
    assert len(agent.transition_matrix) == 5

def test_agent_step_success() -> None:
    config = AgentConfig(agent_id=1, module_id=1, sub_module_id=1)
    agent = FBSAgent(config)

    # Mock transition to guarantee it advances
    agent.transition_matrix[FBSState.REQUIREMENTS][FBSState.FUNCTIONS] = 1.0
    agent.transition_matrix[FBSState.REQUIREMENTS][FBSState.REQUIREMENTS] = 0.0

    advanced, reworked = agent.step(0.5)

    assert advanced is True
    assert reworked is False

def test_agent_stay() -> None:
    config = AgentConfig(agent_id=1, module_id=1, sub_module_id=1)
    agent = FBSAgent(config)

    # Mock transition to guarantee it stays
    agent.transition_matrix[FBSState.REQUIREMENTS][FBSState.FUNCTIONS] = 0.0
    agent.transition_matrix[FBSState.REQUIREMENTS][FBSState.REQUIREMENTS] = 1.0

    advanced, reworked = agent.step(0.5)

    assert advanced is False
    assert reworked is False

def test_agent_rework() -> None:
    config = AgentConfig(agent_id=1, module_id=1, sub_module_id=1)
    agent = FBSAgent(config)
    agent.current_state = FBSState.STRUCTURE

    # Mock transition to guarantee rework to Expected Behavior (Type I/II)
    # S -> Be
    agent.transition_matrix[FBSState.STRUCTURE] = [0.0, 0.0, 1.0, 0.0, 0.0]

    advanced, reworked = agent.step(0.5)

    assert advanced is False
    assert reworked is True
