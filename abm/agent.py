"""
Agent Module for the FBS Markov Model.

BLUEPRINT:
Data Flow:
- An agent holds its own calibrated 5x5 transition matrix.
- Each `step(u)` call processes a uniform random number `u`.
- The matrix dictates transition probabilities to the next state, self-loops, or rework loops.
- `step()` returns a tuple `(advanced, reworked)` to signal progress to the orchestrator.
- Rework updates an internal counter.

Module Boundaries:
- Inputs: `AgentConfig` (dataclass/pydantic model), random draw `u`.
- Outputs: State mutation, boolean flags for orchestrator handling.

Key Interfaces:
- `FBSAgent(config: AgentConfig)`
- `FBSAgent.step(u: float) -> tuple[bool, bool]`
"""

import numpy as np

from abm.config import AgentConfig, FBSState


class FBSAgent:
    """
    An agent modeled as a first-order Markov chain traversing the FBS states.

    This agent uses a 5x5 transition matrix representing Function-Behavior-Structure
    states based on Bott & Mesmer (2019).
    """

    def __init__(self, config: AgentConfig) -> None:
        """Initialize the agent with a calibrated transition matrix."""
        self.agent_id = config.agent_id
        self.module_id = config.module_id
        self.sub_module_id = config.sub_module_id

        self.current_state = FBSState.REQUIREMENTS
        self.rework_count = 0

        # Generate individual matrix based on mean and high CI, applying scaling penalties
        self.transition_matrix = self._generate_matrix(
            config.mean_matrix,
            config.high_matrix,
            config.is_resistant,
            config.resistant_speed_factor,
            config.velocity_modifier,
        )

    def _generate_matrix(
        self,
        mean: list[list[float]],
        high: list[list[float]],
        is_resistant: bool,
        resistant_speed_factor: float,
        velocity_modifier: float,
    ) -> list[list[float]]:
        """
        Generate a stochastic transition matrix for this agent.

        Formula: T_i = mean + rand() * (high - mean).
        Applies resistance and velocity modifiers to transition probabilities.
        Rows must sum to 1.0.
        """
        mat = []
        rng = np.random.default_rng()
        for i in range(len(mean)):
            row = []
            for j in range(len(mean[i])):
                val = mean[i][j] + rng.uniform(0, 1) * (high[i][j] - mean[i][j])

                # Apply scaling modifiers to all state changes (not staying in current state)
                if i != j:
                    val *= velocity_modifier
                    if is_resistant:
                        val *= resistant_speed_factor

                row.append(max(0.0, val))  # ensure no negative probabilities

            # Adjust the "stay" probability (diagonal element) so row sums to 1.0
            diagonal_index = i
            non_diagonal_sum = sum(row) - row[diagonal_index]

            if non_diagonal_sum >= 1.0:
                # If non-diagonal probabilities exceed 1, normalize the whole row
                row_sum = sum(row)
                row = [x / row_sum for x in row]
            else:
                row[diagonal_index] = 1.0 - non_diagonal_sum

            mat.append(row)
        return mat

    def step(self, u: float) -> tuple[bool, bool]:
        """
        Attempt a state transition using random draw u.

        Returns:
            tuple[bool, bool]: (advanced, reworked)
            - advanced: True if the agent moved forward towards D.
            - reworked: True if a rework loop (reformulation) occurred.

        """
        if self.current_state == FBSState.DOCUMENTATION:
            return False, False  # Absorbing state

        row = self.transition_matrix[self.current_state]
        cumulative = 0.0

        # We need to map probability bands to specific transitions.
        # Order of evaluation matters for cumulative probability:
        # Typical order: Forward, Stay, Rework
        # Actually, let's just use the column indices 0..4 directly to build intervals.
        for next_state_int, prob in enumerate(row):
            if prob == 0.0:
                continue  # pragma: no cover

            cumulative += prob
            if u <= cumulative:
                next_state = FBSState(next_state_int)

                if next_state == self.current_state:
                    # Stay
                    return False, False
                if next_state < self.current_state:
                    # Rework
                    self.current_state = next_state
                    self.rework_count += 1
                    return False, True
                # Advance
                self.current_state = next_state
                return True, False

        # Fallback (should not happen if row sums to 1.0)
        return False, False  # pragma: no cover
