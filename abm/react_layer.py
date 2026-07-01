"""
ReAct Layer for AI Agents.

BLUEPRINT:
Data Flow:
- Exposes `ReActGate` which encapsulates the logic to modify transition matrices
  for AI_REACT mode.
- Modifies reformulation (backward) transitions by a smaller factor than raw AI.

Module Boundaries:
- Inputs: Transition matrix (list of list of floats), REACT_REWORK constant.
- Outputs: Modified transition matrix (list of list of floats).

Interfaces:
- `ReActGate`: Pydantic model encapsulating the configuration for ReAct.
- `ReActGate.apply_react(transition_matrix: list[list[float]]) -> list[list[float]]`:
  Applies the reduction to backward/rework edges in the transition matrix.
"""

import copy

from pydantic import BaseModel, ConfigDict

from abm.config import REACT_REWORK, FBSState


class ReActGate(BaseModel):
    """Encapsulates the ReAct logic to mitigate AI stochasticity."""

    model_config = ConfigDict(extra="forbid", strict=True)

    react_rework: float = REACT_REWORK

    def apply_react(self, transition_matrix: list[list[float]]) -> list[list[float]]:
        """
        Apply the ReAct rework multiplier to backward transitions.

        This represents the ReAct Reason->Act->Observe loop catching errors before they
        require major phase rework.
        """
        t_matrix = copy.deepcopy(transition_matrix)

        # Apply to specific known rework transitions based on FBS model
        # S -> Be (Type I/II rework)
        t_matrix[FBSState.STRUCTURE][FBSState.EXPECTED_BEHAVIOR] *= self.react_rework

        # F -> R (Type III rework)
        t_matrix[FBSState.FUNCTIONS][FBSState.REQUIREMENTS] *= self.react_rework

        # S -> S (within-structure rework)
        t_matrix[FBSState.STRUCTURE][FBSState.STRUCTURE] *= self.react_rework

        # Re-normalize diagonal
        for i in range(len(t_matrix)):
            diagonal_index = i
            non_diagonal_sum = sum(t_matrix[i]) - t_matrix[i][diagonal_index]
            if non_diagonal_sum >= 1.0:
                row_sum = sum(t_matrix[i])
                t_matrix[i] = [x / row_sum for x in t_matrix[i]]
            else:
                t_matrix[i][diagonal_index] = 1.0 - non_diagonal_sum

        return t_matrix
