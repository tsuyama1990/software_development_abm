"""
AI Modifier Layer for the FBS Markov Model.

BLUEPRINT:
Data Flow:
- Exposes `apply_ai_modifiers` function.
- Takes an agent's base transition matrix and their AI mode.
- Computes AI_SPEED speedups and AI_REWORK penalties.
- Delegates to `ReActGate` if mode is AI_REACT.
- Clamps probabilities to [0, 1] and normalizes rows.

Module Boundaries:
- Inputs: `transition_matrix` (5x5 matrix), `ai_mode` (AIMode).
- Outputs: `transition_matrix` (modified, 5x5).

Interfaces:
- `apply_ai_modifiers(transition_matrix: list[list[float]], ai_mode: AIMode) -> list[list[float]]`
"""

import copy

from abm.config import AI_REWORK, AI_SPEED, AIMode, FBSState
from abm.react_layer import ReActGate


def apply_ai_modifiers(transition_matrix: list[list[float]], ai_mode: AIMode) -> list[list[float]]:
    """
    Apply AI speed and rework modifiers to a given transition matrix.

    If NO_AI, returns an unmodified copy.
    If AI_RAW, applies high speed and high rework modifiers.
    If AI_REACT, applies high speed, but uses ReActGate for mitigated rework.
    """
    if ai_mode == AIMode.NO_AI:
        return copy.deepcopy(transition_matrix)

    t_matrix = copy.deepcopy(transition_matrix)

    # Both AI_RAW and AI_REACT get the speed boost for forward transitions
    t_matrix[FBSState.REQUIREMENTS][FBSState.FUNCTIONS] *= AI_SPEED
    t_matrix[FBSState.FUNCTIONS][FBSState.EXPECTED_BEHAVIOR] *= AI_SPEED
    t_matrix[FBSState.EXPECTED_BEHAVIOR][FBSState.STRUCTURE] *= AI_SPEED
    t_matrix[FBSState.STRUCTURE][FBSState.DOCUMENTATION] *= AI_SPEED

    if ai_mode == AIMode.AI_RAW:
        # High unmitigated rework
        t_matrix[FBSState.STRUCTURE][FBSState.EXPECTED_BEHAVIOR] *= AI_REWORK
        t_matrix[FBSState.FUNCTIONS][FBSState.REQUIREMENTS] *= AI_REWORK
        t_matrix[FBSState.STRUCTURE][FBSState.STRUCTURE] *= AI_REWORK
    elif ai_mode == AIMode.AI_REACT:
        # Apply ReAct logic for rework mitigation
        react_gate = ReActGate()
        t_matrix = react_gate.apply_react(t_matrix)

    # Normalize rows
    for i in range(len(t_matrix)):
        # Apply clipping to non-diagonal elements
        for j in range(len(t_matrix[i])):
            if i != j:
                t_matrix[i][j] = min(1.0, max(0.0, t_matrix[i][j]))

        diagonal_index = i
        non_diagonal_sum = sum(t_matrix[i]) - t_matrix[i][diagonal_index]

        if non_diagonal_sum >= 1.0:
            # If non-diagonal probabilities exceed 1, normalize the whole row
            row_sum = sum(t_matrix[i])
            t_matrix[i] = [x / row_sum for x in t_matrix[i]]
        else:
            t_matrix[i][diagonal_index] = 1.0 - non_diagonal_sum
            # Clip diagonal element just in case
            t_matrix[i][diagonal_index] = min(1.0, max(0.0, t_matrix[i][diagonal_index]))

    return t_matrix
